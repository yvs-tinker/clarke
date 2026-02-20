"""MedASR model wrapper with mock-mode fallback transcription."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import librosa
try:
    from transformers import pipeline
except ModuleNotFoundError:  # pragma: no cover - mock mode support
    pipeline = None

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
        """Load the MedASR transformer pipeline unless running in mock mode.

        Args:
            None: Uses settings for model id and device selection.

        Returns:
            None: Caches loaded pipeline instance.
        """
        if self.is_mock_mode:
            self._pipeline = "mock"
            self.model_manager.register_model("medasr", self._pipeline)
            return

        if self._pipeline is not None:
            return

        if pipeline is None:
            raise ModelExecutionError("transformers is required for non-mock MedASR mode")

        device = "cuda:0"
        if self.model_manager.check_gpu()["vram_total_bytes"] == 0:
            device = "cpu"

        try:
            self._pipeline = pipeline(
                "automatic-speech-recognition",
                model=self.settings.MEDASR_MODEL_ID,
                device=device,
            )
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

        waveform, _ = librosa.load(source, sr=16000, mono=True)
        duration_s = float(librosa.get_duration(y=waveform, sr=16000))

        try:
            result = self._pipeline(
                waveform,
                chunk_length_s=20,
                stride_length_s=(4, 2),
                return_timestamps=True,
                generate_kwargs={"language": "en", "task": "transcribe"},
            )
        except Exception as exc:
            raise ModelExecutionError(f"MedASR inference failed: {exc}") from exc

        transcript_text = str(result.get("text", "")).strip()
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
        """Compute audio duration in seconds using librosa.

        Args:
            audio_path (Path): Audio file path.

        Returns:
            float: Duration in seconds.
        """
        waveform, sample_rate = librosa.load(audio_path, sr=16000, mono=True)
        return float(librosa.get_duration(y=waveform, sr=sample_rate))

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
