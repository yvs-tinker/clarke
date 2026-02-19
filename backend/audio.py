"""Audio conversion and validation utilities for MedASR-ready WAV files."""

from __future__ import annotations

from pathlib import Path

import librosa
from pydub import AudioSegment

from backend.errors import AudioError


MIN_AUDIO_DURATION_S = 5.0
MAX_AUDIO_DURATION_S = 1800.0
EXPECTED_SAMPLE_RATE = 16000
EXPECTED_CHANNELS = 1


def convert_to_wav_16k(input_path: str, output_path: str) -> str:
    """Convert supported audio input to 16kHz mono PCM WAV.

    Args:
        input_path (str): Source audio path (e.g. webm, mp3, wav).
        output_path (str): Destination WAV path.

    Returns:
        str: Output path for converted 16kHz mono WAV file.
    """
    source_path = Path(input_path)
    destination_path = Path(output_path)

    if not source_path.exists():
        raise AudioError(f"Audio input not found: {source_path}")

    try:
        audio = AudioSegment.from_file(source_path)
    except Exception as exc:  # pragma: no cover - pydub/ffmpeg message is external
        raise AudioError(f"Failed to decode audio file {source_path}: {exc}") from exc

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    processed = audio.set_frame_rate(EXPECTED_SAMPLE_RATE).set_channels(EXPECTED_CHANNELS).set_sample_width(2)

    try:
        processed.export(destination_path, format="wav")
    except Exception as exc:  # pragma: no cover - pydub/ffmpeg message is external
        raise AudioError(f"Failed to export WAV audio {destination_path}: {exc}") from exc

    return str(destination_path)


def validate_audio(file_path: str) -> dict[str, float | int]:
    """Validate an audio file meets pipeline constraints.

    Args:
        file_path (str): Path to WAV file to inspect.

    Returns:
        dict[str, float | int]: duration_s, sample_rate, channels values.
    """
    path = Path(file_path)
    if not path.exists():
        raise AudioError(f"Audio file not found: {path}")

    try:
        waveform, sample_rate = librosa.load(path, sr=None, mono=False)
    except Exception as exc:
        raise AudioError(f"Unable to load audio for validation: {path}: {exc}") from exc

    channels = int(waveform.shape[0]) if getattr(waveform, "ndim", 1) > 1 else 1
    duration_s = float(librosa.get_duration(y=waveform, sr=sample_rate))

    if sample_rate != EXPECTED_SAMPLE_RATE:
        raise AudioError(f"Invalid sample rate {sample_rate}; expected {EXPECTED_SAMPLE_RATE}")
    if channels != EXPECTED_CHANNELS:
        raise AudioError(f"Invalid channel count {channels}; expected {EXPECTED_CHANNELS}")
    if duration_s <= MIN_AUDIO_DURATION_S:
        raise AudioError(f"Audio duration {duration_s:.2f}s must be > {MIN_AUDIO_DURATION_S}s")
    if duration_s >= MAX_AUDIO_DURATION_S:
        raise AudioError(f"Audio duration {duration_s:.2f}s must be < {MAX_AUDIO_DURATION_S}s")

    return {
        "duration_s": duration_s,
        "sample_rate": int(sample_rate),
        "channels": channels,
    }
