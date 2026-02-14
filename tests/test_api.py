"""Tests for Clarke FastAPI health and audio upload endpoints."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from fastapi.testclient import TestClient

from backend import api


def _make_wav_file(path: Path, duration_s: float = 6.0, sample_rate: int = 16000) -> Path:
    """Create a mono PCM WAV test file with a simple sine wave.

    Args:
        path (Path): Destination file path.
        duration_s (float): Audio duration in seconds.
        sample_rate (int): Sampling rate for generated waveform.

    Returns:
        Path: Path to generated WAV file.
    """

    total_samples = int(duration_s * sample_rate)
    amplitude = 12000
    frequency_hz = 440.0

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for sample_index in range(total_samples):
            sample_value = int(amplitude * math.sin(2.0 * math.pi * frequency_hz * sample_index / sample_rate))
            frames.extend(struct.pack("<h", sample_value))
        wav_file.writeframes(bytes(frames))

    return path


def test_health_endpoint_returns_expected_schema() -> None:
    """Verify health endpoint returns status payload with required top-level keys.

    Args:
        None: Uses test client against in-process FastAPI app.

    Returns:
        None: Assertions validate response schema shape.
    """

    client = TestClient(api.app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "models" in payload
    assert "medasr" in payload["models"]
    assert "fhir" in payload
    assert "gpu" in payload
    assert "timestamp" in payload


def test_audio_upload_accepts_wav_and_returns_duration(tmp_path: Path) -> None:
    """Verify audio upload endpoint stores WAV and returns duration metadata.

    Args:
        tmp_path (Path): Temporary directory for test WAV generation.

    Returns:
        None: Assertions validate upload success and response fields.
    """

    client = TestClient(api.app)
    wav_path = _make_wav_file(tmp_path / "sample.wav")

    with wav_path.open("rb") as audio_stream:
        response = client.post(
            "/api/v1/consultations/test-001/audio",
            files={"audio_file": ("sample.wav", audio_stream, "audio/wav")},
            data={"is_final": "true"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["consultation_id"] == "test-001"
    assert payload["audio_received"] is True
    assert payload["duration_s"] > 5.0
