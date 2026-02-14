"""Tests for MedASR mock transcription and audio preprocessing utilities."""

from __future__ import annotations

import wave
from pathlib import Path

import pytest

from backend.audio import convert_to_wav_16k, validate_audio
from backend.config import get_settings
from backend.errors import AudioError
from backend.models.medasr import MedASRModel


def _create_wav(path: Path, sample_rate: int, channels: int, duration_s: int) -> None:
    """Create a deterministic silent PCM WAV file for tests.

    Args:
        path (Path): Destination WAV path.
        sample_rate (int): Output sample rate in Hz.
        channels (int): Output channel count.
        duration_s (int): Duration in seconds.

    Returns:
        None: Writes WAV bytes to disk.
    """
    n_frames = sample_rate * duration_s
    sample_width = 2
    silence_frame = (0).to_bytes(sample_width, byteorder="little", signed=True)
    frame_data = silence_frame * channels * n_frames

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(sample_rate)
        handle.writeframes(frame_data)


def test_convert_and_validate_audio_success(tmp_path: Path) -> None:
    """Ensure conversion produces a valid 16kHz mono WAV accepted by validation.

    Args:
        tmp_path (Path): Temporary test directory root.

    Returns:
        None: Assertions validate conversion + validation contract.
    """
    source = tmp_path / "source.wav"
    output = tmp_path / "converted.wav"

    _create_wav(source, sample_rate=22050, channels=2, duration_s=8)
    converted_path = convert_to_wav_16k(str(source), str(output))
    metadata = validate_audio(converted_path)

    assert metadata["sample_rate"] == 16000
    assert metadata["channels"] == 1
    assert metadata["duration_s"] > 5


def test_validate_audio_raises_for_short_duration(tmp_path: Path) -> None:
    """Ensure validation rejects too-short inputs per PRD constraints.

    Args:
        tmp_path (Path): Temporary test directory root.

    Returns:
        None: Expects AudioError to be raised.
    """
    short_wav = tmp_path / "short.wav"
    _create_wav(short_wav, sample_rate=16000, channels=1, duration_s=2)

    with pytest.raises(AudioError):
        validate_audio(str(short_wav))


def test_medasr_mock_transcribe_reads_demo_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure mock mode returns demo transcript text for known demo audio.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for temporary env overrides.

    Returns:
        None: Assertions validate mock transcript loading.
    """
    monkeypatch.setenv("MEDASR_MODEL_ID", "mock")
    get_settings.cache_clear()

    model = MedASRModel()
    transcript = model.transcribe("data/demo/mrs_thompson.wav")

    assert "HbA1c" in transcript.text
    assert transcript.word_count > 20
    assert transcript.consultation_id == "mrs_thompson"
