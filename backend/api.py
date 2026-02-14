"""FastAPI API surface for Clarke consultation and health endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfileobj
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from backend.audio import convert_to_wav_16k, validate_audio
from backend.config import get_settings
from backend.errors import AudioError, get_component_logger
from backend.models.medasr import MedASRModel
from backend.models.model_manager import ModelManager

app = FastAPI(title="Clarke API", version="0.1.0")
settings = get_settings()
logger = get_component_logger("api")
model_manager = ModelManager()
medasr_model = MedASRModel(model_manager=model_manager)
consultation_store: dict[str, dict[str, Any]] = {}


def _iso_timestamp() -> str:
    """Return UTC timestamp in ISO 8601 format with Z suffix.

    Args:
        None: No input parameters.

    Returns:
        str: UTC timestamp string.
    """

    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _health_fhir_status() -> dict[str, Any]:
    """Compute lightweight FHIR service health metadata for health endpoint.

    Args:
        None: Reads settings and local data fixtures.

    Returns:
        dict[str, Any]: FHIR connectivity status and available patient count.
    """

    clinic_list_path = Path("data/clinic_list.json")
    if settings.USE_MOCK_FHIR and clinic_list_path.exists():
        import json

        payload = json.loads(clinic_list_path.read_text(encoding="utf-8"))
        patients = payload.get("patients", [])
        return {"status": "connected", "patient_count": len(patients)}

    return {"status": "unknown", "patient_count": 0}


def _save_upload_temp(upload: UploadFile, destination: Path) -> Path:
    """Persist an uploaded file to disk for subsequent conversion/validation.

    Args:
        upload (UploadFile): Uploaded file object from multipart payload.
        destination (Path): Output path for storing file bytes.

    Returns:
        Path: Saved destination path.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output_stream:
        copyfileobj(upload.file, output_stream)
    return destination


@app.get("/api/v1/health")
def get_health() -> dict[str, Any]:
    """Return current service, model, and GPU health state.

    Args:
        None: Uses process-level singletons for status.

    Returns:
        dict[str, Any]: Health response payload.
    """

    gpu_info = model_manager.check_gpu()
    models = {
        "medasr": {
            "loaded": model_manager.get_model("medasr") is not None,
            "device": "cuda:0" if gpu_info["vram_total_bytes"] > 0 else "cpu",
        },
        "medgemma_4b": {"loaded": False, "device": "n/a", "quantised": "4bit"},
        "medgemma_27b": {"loaded": False, "device": "n/a", "quantised": "4bit"},
    }

    return {
        "status": "healthy",
        "models": models,
        "fhir": _health_fhir_status(),
        "gpu": {
            "name": gpu_info["gpu_name"],
            "vram_used_gb": round(float(gpu_info["vram_used_bytes"]) / 1_000_000_000, 2),
            "vram_total_gb": round(float(gpu_info["vram_total_bytes"]) / 1_000_000_000, 2),
        },
        "timestamp": _iso_timestamp(),
    }


@app.post("/api/v1/consultations/{consultation_id}/audio")
def upload_audio(
    consultation_id: str,
    audio_file: UploadFile = File(...),
    is_final: bool = Form(...),
) -> dict[str, Any]:
    """Accept consultation audio, convert to MedASR format, and store metadata.

    Args:
        consultation_id (str): Consultation identifier.
        audio_file (UploadFile): Uploaded WAV/WebM audio file.
        is_final (bool): Whether upload is the final complete recording.

    Returns:
        dict[str, Any]: Upload acknowledgement and validated duration seconds.
    """

    extension = Path(audio_file.filename or "").suffix.lower()
    if extension not in {".wav", ".webm"}:
        raise HTTPException(status_code=400, detail="Only WAV or WebM audio uploads are supported")

    uploads_root = Path("data/uploads") / consultation_id
    raw_path = uploads_root / f"raw{extension}"
    wav_path = uploads_root / "audio_16k.wav"

    try:
        _save_upload_temp(audio_file, raw_path)
        processed_path = raw_path if extension == ".wav" else Path(convert_to_wav_16k(str(raw_path), str(wav_path)))
        if extension == ".wav":
            processed_path = Path(convert_to_wav_16k(str(raw_path), str(wav_path)))

        audio_metadata = validate_audio(str(processed_path))
    except AudioError as exc:
        logger.error("Audio processing failed", consultation_id=consultation_id, error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    consultation_store[consultation_id] = {
        "audio_file_path": str(processed_path),
        "is_final": is_final,
        "duration_s": audio_metadata["duration_s"],
        "updated_at": _iso_timestamp(),
    }

    logger.info(
        "Stored consultation audio",
        consultation_id=consultation_id,
        duration_s=audio_metadata["duration_s"],
        is_final=is_final,
    )

    return {
        "consultation_id": consultation_id,
        "audio_received": True,
        "duration_s": audio_metadata["duration_s"],
    }
