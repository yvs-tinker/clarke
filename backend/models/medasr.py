"""MedASR model wrapper with mock-mode fallback transcription."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import librosa
try:
    import torch
    from transformers import AutoProcessor, AutoModelForCTC
except ModuleNotFoundError:
    torch = None
    AutoProcessor = None
    AutoModelForCTC = None

from backend.config import get_settings
from backend.errors import ModelExecutionError
from backend.models.model_manager import ModelManager
from backend.schemas import Transcript


class MedASRModel:
    """Load and run MedASR speech recognition or a deterministic mock implementation."""

    def __init__(self, model_manager: ModelManager | None = None) -> None:
        self.settings = get_settings()
        self.model_manager = model_manager or ModelManager()
        self._model = None
        self._processor = None
        self._device = "cpu"

    @property
    def is_mock_mode(self) -> bool:
        return self.settings.MEDASR_MODEL_ID.lower() == "mock"

    def load_model(self) -> None:
        if self.is_mock_mode:
            self._model = "mock"
            self.model_manager.register_model("medasr", self._model)
            return

        if self._model is not None:
            return

        if AutoModelForCTC is None:
            raise ModelExecutionError("transformers is required for non-mock MedASR mode")

        device = "cuda:0"
        if self.model_manager.check_gpu()["vram_total_bytes"] == 0:
            device = "cpu"

        model_id = self.settings.MEDASR_MODEL_ID

        try:
            self._processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            self._model = AutoModelForCTC.from_pretrained(model_id, trust_remote_code=True)
            self._model = self._model.to(device)
            self._model.eval()
            self._device = device
        except Exception as exc:
            raise ModelExecutionError(f"Failed to load MedASR model: {exc}") from exc

        self.model_manager.register_model("medasr", self._model)

    def transcribe(self, audio_path: str) -> Transcript:
        source = Path(audio_path)
        if not source.exists():
            raise ModelExecutionError(f"Audio path not found: {source}")

        if self._model is None:
            self.load_model()

        if self.is_mock_mode:
            text = self._get_mock_text(source)
            duration_s = self._duration(source)
            return self._make_transcript(source, text, duration_s)

        waveform, _ = librosa.load(source, sr=16000, mono=True)
        duration_s = float(librosa.get_duration(y=waveform, sr=16000))

        try:
            inputs = self._processor(
                waveform,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True,
            )
            inputs = inputs.to(self._device)

            with torch.no_grad():
                outputs = self._model.generate(**inputs)
                transcript_text = self._processor.batch_decode(outputs, skip_special_tokens=True)[0]

            # Clean up special tokens that may remain
            import re
            transcript_text = transcript_text.replace("<epsilon>", "")
            transcript_text = transcript_text.replace("</s>", "").replace("<s>", "")
            transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()

        except Exception as exc:
            raise ModelExecutionError(f"MedASR inference failed: {exc}") from exc

        return self._make_transcript(source, transcript_text, duration_s)

    def _make_transcript(self, audio_path: Path, text: str, duration_s: float) -> Transcript:
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
        waveform, sample_rate = librosa.load(audio_path, sr=16000, mono=True)
        return float(librosa.get_duration(y=waveform, sr=sample_rate))

    @staticmethod
    def _get_mock_text(audio_path: Path) -> str:
        transcript_map = {
            "mrs_thompson": Path("data/demo/mrs_thompson_transcript.txt"),
            "mr_okafor": Path("data/demo/mr_okafor_transcript.txt"),
            "ms_patel": Path("data/demo/ms_patel_transcript.txt"),
            "mr_williams": Path("data/demo/mr_williams_transcript.txt"),
            "mrs_khan": Path("data/demo/mrs_khan_transcript.txt"),
        }
        for key, transcript_path in transcript_map.items():
            if key in audio_path.stem:
                if transcript_path.exists():
                    return transcript_path.read_text(encoding="utf-8").strip()
        return "Mock transcript placeholder for non-demo audio input."
