"""MedASR model wrapper with mock-mode fallback transcription."""

from __future__ import annotations

import logging
import re as _re
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
    AutoModelForCTC = None

from backend.config import get_settings
from backend.errors import ModelExecutionError
from backend.models.model_manager import ModelManager
from backend.schemas import Transcript

logger = logging.getLogger("clarke.medasr")


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

        model_id = self.settings.MEDASR_MODEL_ID

        try:
            # ---------- DEBUG: Log transformers version ----------
            import transformers
            logger.info("[MedASR-DEBUG] transformers version: %s", transformers.__version__)
            logger.info("[MedASR-DEBUG] Loading model_id=%s on device=%s", model_id, device)

            # ---------- Load processor ----------
            self._processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            logger.info("[MedASR-DEBUG] Processor type: %s", type(self._processor).__name__)

            # Log processor internals
            fe = getattr(self._processor, "feature_extractor", self._processor)
            logger.info("[MedASR-DEBUG] Feature extractor type: %s", type(fe).__name__)
            if hasattr(fe, "sampling_rate"):
                logger.info("[MedASR-DEBUG] Feature extractor sampling_rate: %s", fe.sampling_rate)
            if hasattr(fe, "feature_size"):
                logger.info("[MedASR-DEBUG] Feature extractor feature_size: %s", fe.feature_size)

            # ---------- Load model ----------
            model = AutoModelForCTC.from_pretrained(model_id, trust_remote_code=True)
            model = model.to(device)
            model.eval()
            self._device = device

            # ---------- DEBUG: Log model capabilities ----------
            logger.info("[MedASR-DEBUG] Model type: %s", type(model).__name__)
            logger.info("[MedASR-DEBUG] Model has .generate(): %s", hasattr(model, "generate"))
            if hasattr(model, "config"):
                config = model.config
                logger.info("[MedASR-DEBUG] vocab_size: %s", getattr(config, "vocab_size", "N/A"))
                logger.info("[MedASR-DEBUG] ctc_blank_id: %s", getattr(config, "ctc_blank_id", "N/A"))
                logger.info("[MedASR-DEBUG] pad_token_id: %s", getattr(config, "pad_token_id", "N/A"))

            self._pipeline = model

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

        # =====================================================================
        # STEP 1: Load and preprocess audio
        # =====================================================================
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

        logger.info("[MedASR-DEBUG] Audio loaded: samples=%d, duration=%.2fs, sr_orig=%d, dtype=%s",
                     len(waveform), duration_s, file_sr, waveform.dtype)
        logger.info("[MedASR-DEBUG] Waveform stats: min=%.6f, max=%.6f, mean=%.6f, std=%.6f",
                     waveform.min(), waveform.max(), waveform.mean(), waveform.std())

        try:
            # =================================================================
            # STEP 2: Run processor
            # =================================================================
            inputs = self._processor(
                waveform,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True,
            )

            # ---------- DEBUG: Log processor output ----------
            logger.info("[MedASR-DEBUG] Processor output keys: %s", list(inputs.data.keys()))
            for key, val in inputs.data.items():
                if hasattr(val, "shape"):
                    logger.info("[MedASR-DEBUG]   %s: shape=%s, dtype=%s, min=%.6f, max=%.6f",
                                 key, val.shape, val.dtype, val.float().min().item(), val.float().max().item())

            # =================================================================
            # STEP 3: Move inputs to device
            # =================================================================
            # Official Google approach: move entire inputs object to device
            inputs = inputs.to(self._device)
            logger.info("[MedASR-DEBUG] Inputs moved to device: %s", self._device)

            # =================================================================
            # STEP 4: Run inference — prefer model.generate() (official method)
            # =================================================================
            model = self._pipeline

            if hasattr(model, "generate"):
                # ----- PRIMARY PATH: model.generate() (official Google method) -----
                logger.info("[MedASR-DEBUG] Using model.generate() (official inference path)")
                with torch.no_grad():
                    outputs = model.generate(**inputs)

                logger.info("[MedASR-DEBUG] generate() output type: %s", type(outputs).__name__)
                if hasattr(outputs, "shape"):
                    logger.info("[MedASR-DEBUG] generate() output shape: %s", outputs.shape)
                elif isinstance(outputs, (list, tuple)):
                    logger.info("[MedASR-DEBUG] generate() output length: %d", len(outputs))
                    if len(outputs) > 0 and hasattr(outputs[0], "shape"):
                        logger.info("[MedASR-DEBUG] generate() output[0] shape: %s", outputs[0].shape)

                # Log first 20 token IDs for debugging
                if hasattr(outputs, "shape") and outputs.numel() > 0:
                    ids_preview = outputs[0][:20].tolist()
                    logger.info("[MedASR-DEBUG] First 20 generated token IDs: %s", ids_preview)

                transcript_text = self._processor.batch_decode(outputs)[0]
                logger.info("[MedASR-DEBUG] batch_decode raw output: '%s'", transcript_text[:200])

            else:
                # ----- FALLBACK: Manual CTC decoding -----
                logger.warning("[MedASR-DEBUG] model.generate() NOT available — using manual CTC fallback")
                transcript_text = self._manual_ctc_decode(model, inputs)

            # =================================================================
            # STEP 5: Clean up transcript text
            # =================================================================
            transcript_text = transcript_text.replace("<epsilon>", "").replace("</s>", "").replace("<s>", "").strip()
            transcript_text = _re.sub(r'\s+', ' ', transcript_text)

            logger.info("[MedASR-DEBUG] Final transcript (%d chars, %d words): '%s'",
                         len(transcript_text), len(transcript_text.split()), transcript_text[:300])

        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            raise ModelExecutionError(f"MedASR inference failed: {exc}\nTraceback:\n{tb}") from exc

        return self._make_transcript(source, transcript_text, duration_s)

    def _manual_ctc_decode(self, model, inputs) -> str:
        """Fallback manual CTC decoding when model.generate() is unavailable.

        Args:
            model: The loaded CTC model.
            inputs: Preprocessed inputs from the processor.

        Returns:
            str: Decoded transcript text.
        """
        # Identify the input key
        input_key = list(inputs.data.keys())[0]
        model_input = inputs[input_key].float()
        logger.info("[MedASR-DEBUG] Manual CTC: input_key=%s, shape=%s", input_key, model_input.shape)

        with torch.no_grad():
            output = model(**{input_key: model_input})
            logits = output.logits

        logger.info("[MedASR-DEBUG] Logits shape: %s", logits.shape)
        logger.info("[MedASR-DEBUG] Logits stats: min=%.4f, max=%.4f, mean=%.4f",
                     logits.min().item(), logits.max().item(), logits.mean().item())

        # Check if logits are degenerate (all same value = model not working)
        logit_std = logits.std().item()
        logger.info("[MedASR-DEBUG] Logits std: %.6f (if ~0, model output is degenerate)", logit_std)

        predicted_ids = torch.argmax(logits, dim=-1)
        ids = predicted_ids[0].tolist()

        # Log token distribution
        from collections import Counter
        id_counts = Counter(ids)
        most_common = id_counts.most_common(5)
        logger.info("[MedASR-DEBUG] Top 5 predicted token IDs: %s", most_common)
        logger.info("[MedASR-DEBUG] Total frames: %d, unique tokens: %d", len(ids), len(id_counts))

        # CTC collapse
        collapsed = []
        prev = None
        for t in ids:
            if t != prev:
                collapsed.append(t)
            prev = t

        blank_id = getattr(model.config, 'ctc_blank_id', 0)
        logger.info("[MedASR-DEBUG] Using blank_id=%d", blank_id)

        pre_blank_len = len(collapsed)
        collapsed = [t for t in collapsed if t != blank_id]
        logger.info("[MedASR-DEBUG] CTC collapse: %d frames -> %d unique -> %d after blank removal",
                     len(ids), pre_blank_len, len(collapsed))

        if not collapsed:
            logger.warning("[MedASR-DEBUG] ALL tokens were blank! Model produced no speech output.")
            return ""

        logger.info("[MedASR-DEBUG] First 20 collapsed token IDs: %s", collapsed[:20])

        collapsed_tensor = torch.tensor([collapsed], dtype=predicted_ids.dtype)
        raw_text = self._processor.batch_decode(collapsed_tensor)[0]
        logger.info("[MedASR-DEBUG] Manual CTC raw decode: '%s'", raw_text[:200])

        return raw_text

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
