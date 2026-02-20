"""MedASR model wrapper with mock-mode fallback transcription."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import soundfile as sf
import numpy as np
try:
    import torch
    from transformers import AutoProcessor, AutoModelForCTC
except ModuleNotFoundError:  # pragma: no cover - mock mode support
    torch = None
    AutoProcessor = None
    Wav2Vec2Processor = None
    Wav2Vec2Processor = None
    AutoModelForCTC = None

from backend.config import get_settings
from backend.errors import ModelExecutionError
from backend.models.model_manager import ModelManager
from backend.schemas import Transcript


class MedASRModel:
    """Load and run MedASR speech recognition or a deterministic mock implementation.

    Args:
        model_manager (ModelManager | None): Optional shared model registry manager.

    Returns:
        None: Initialised model wrapper with lazy-loaded pipeline.
    """

    def __init__(self, model_manager: ModelManager | None = None) -> None:
        """Initialise MedASR wrapper.

        Args:
            model_manager (ModelManager | None): Optional model manager instance.

        Returns:
            None: Sets internal settings and model state.
        """
        self.settings = get_settings()
        self.model_manager = model_manager or ModelManager()
        self._pipeline = None
        self._processor = None
        self._device = "cpu"

    @property
    def is_mock_mode(self) -> bool:
        """Return whether MedASR should operate in deterministic mock mode.

        Args:
            None: Reads current settings.

        Returns:
            bool: True when configured model id is "mock".
        """
        return self.settings.MEDASR_MODEL_ID.lower() == "mock"

    def load_model(self) -> None:
        """Load the MedASR model and processor unless running in mock mode.

        Args:
            None: Uses settings for model id and device selection.

        Returns:
            None: Caches loaded model and processor instances.
        """
        if self.is_mock_mode:
            self._pipeline = "mock"
            self.model_manager.register_model("medasr", self._pipeline)
            return

        if self._pipeline is not None:
            return

        if AutoModelForCTC is None:
            raise ModelExecutionError("transformers is required for non-mock MedASR mode")

        device = "cuda:0"
        if self.model_manager.check_gpu()["vram_total_bytes"] == 0:
            device = "cpu"

        try:
            try:
                self._processor = Wav2Vec2Processor.from_pretrained(self.settings.MEDASR_MODEL_ID, trust_remote_code=True)
            except Exception:
                try:
                    self._processor = AutoFeatureExtractor.from_pretrained(self.settings.MEDASR_MODEL_ID, trust_remote_code=True)
                except Exception:
                    self._processor = AutoProcessor.from_pretrained(self.settings.MEDASR_MODEL_ID, trust_remote_code=True)
            model = AutoModelForCTC.from_pretrained(self.settings.MEDASR_MODEL_ID, trust_remote_code=True)
            model = model.to(device)
            model.eval()
            self._device = device

            # Monkey-patch: newer transformers passes extra arg to _torch_extract_fbank_features
            fe = getattr(self._processor, "feature_extractor", self._processor)
            if hasattr(fe, "_torch_extract_fbank_features"):
                _orig_fn = fe._torch_extract_fbank_features
                import inspect
                if len(inspect.signature(_orig_fn).parameters) < 3:
                    def _patched(waveform, device=None, center=None):
                        return _orig_fn(waveform) if device is None else _orig_fn(waveform, device)
                    fe._torch_extract_fbank_features = _patched
            self._pipeline = model  # store model here so is_mock_mode / None checks still work
        except Exception as exc:
            raise ModelExecutionError(f"Failed to load MedASR model: {exc}") from exc

        self.model_manager.register_model("medasr", self._pipeline)

    def transcribe(self, audio_path: str) -> Transcript:
        """Transcribe audio input into a Transcript schema object.

        Args:
            audio_path (str): Path to 16kHz mono audio WAV.

        Returns:
            Transcript: Structured transcript result.
        """
        source = Path(audio_path)
        if not source.exists():
            raise ModelExecutionError(f"Audio path not found: {source}")

        if self._pipeline is None:
            self.load_model()

        if self.is_mock_mode:
            text = self._get_mock_text(source)
            duration_s = self._duration(source)
            return self._make_transcript(source, text, duration_s)

        waveform, file_sr = sf.read(source, dtype="float32", always_2d=False)
        # Convert to mono if stereo
        if waveform.ndim > 1:
            waveform = waveform.mean(axis=1)
        # Resample if needed
        if file_sr != 16000:
            from scipy.signal import resample

            num_samples = int(len(waveform) * 16000 / file_sr)
            waveform = resample(waveform, num_samples).astype(np.float32)
        duration_s = float(len(waveform)) / 16000.0

        try:
            inputs = self._processor(
                waveform,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True,
            )
            # MedASR processor may return input_features or input_values
            if hasattr(inputs, "input_features") and inputs.input_features is not None:
                model_input = inputs.input_features.to(self._device)
            elif hasattr(inputs, "input_values") and inputs.input_values is not None:
                model_input = inputs.input_values.to(self._device)
            else:
                # Fallback: get first tensor from the batch encoding
                key = list(inputs.data.keys())[0]
                model_input = inputs[key].to(self._device)

            with torch.no_grad():
                model_input = model_input.float()
                logits = self._pipeline(**{list(inputs.data.keys())[0]: model_input}).logits

            predicted_ids = torch.argmax(logits, dim=-1)

            # CTC decoding: collapse consecutive duplicate tokens, then remove blanks
            ids = predicted_ids[0].tolist()
            collapsed = []
            prev = None
            for t in ids:
                if t != prev:
                    collapsed.append(t)
                prev = t
            # Token 0 is the CTC blank in most CTC models
            blank_id = getattr(self._pipeline.config, 'ctc_blank_id', 0)
            collapsed = [t for t in collapsed if t != blank_id]
            collapsed_tensor = torch.tensor([collapsed], dtype=predicted_ids.dtype)

            raw_text = self._processor.batch_decode(collapsed_tensor)[0]
            # Strip any remaining special tokens
            transcript_text = raw_text.replace("<epsilon>", "").replace("</s>", "").replace("<s>", "").strip()
            # Collapse multiple spaces
            import re as _re

            transcript_text = _re.sub(r'\s+', ' ', transcript_text)
        except Exception as exc:
            import traceback

            tb = traceback.format_exc()
            raise ModelExecutionError(f"MedASR inference failed: {exc}\nTraceback:\n{tb}") from exc
        return self._make_transcript(source, transcript_text, duration_s)

    def _make_transcript(self, audio_path: Path, text: str, duration_s: float) -> Transcript:
        """Build a Transcript object from model output values.

        Args:
            audio_path (Path): Source audio path.
            text (str): Transcript text.
            duration_s (float): Audio duration seconds.

        Returns:
            Transcript: Pydantic transcript model.
        """
        now = datetime.now(tz=timezone.utc).isoformat()
        consultation_id = audio_path.stem
        return Transcript(
            consultation_id=consultation_id,
            text=text,
            duration_s=duration_s,
            word_count=len(text.split()),
            created_at=now,
        )

    @staticmethod
    def _duration(audio_path: Path) -> float:
        """Compute audio duration in seconds using soundfile.

        Args:
            audio_path (Path): Audio file path.

        Returns:
            float: Duration in seconds.
        """
        info = sf.info(audio_path)
        return float(info.frames) / float(info.samplerate)

    @staticmethod
    def _get_mock_text(audio_path: Path) -> str:
        """Return ground-truth transcript for known demo files in mock mode.

        Args:
            audio_path (Path): Audio file path used for lookup.

        Returns:
            str: Transcript text from fixture file or fallback placeholder.
        """
        transcript_map = {
            "mrs_thompson": Path("data/demo/mrs_thompson_transcript.txt"),
            "mr_okafor": Path("data/demo/mr_okafor_transcript.txt"),
            "ms_patel": Path("data/demo/ms_patel_transcript.txt"),
        }
        for key, transcript_path in transcript_map.items():
            if key in audio_path.stem:
                return transcript_path.read_text(encoding="utf-8").strip()
        return "Mock transcript placeholder for non-demo audio input."
