"""FastAPI API surface for Clarke consultation and health endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfileobj
from typing import Any

from fastapi import BackgroundTasks, Body, FastAPI, File, Form, HTTPException, UploadFile

from backend.audio import convert_to_wav_16k, validate_audio
from backend.config import get_settings
from backend.errors import AudioError, ModelExecutionError, get_component_logger
from backend.orchestrator import PipelineOrchestrator
from backend.schemas import ConsultationStatus, Patient

app = FastAPI(title="Clarke API", version="0.1.0")
settings = get_settings()
logger = get_component_logger("api")
orchestrator = PipelineOrchestrator()


def _iso_timestamp() -> str:
    """Return UTC timestamp in ISO 8601 format with Z suffix.

    Args:
        None: No input parameters.

    Returns:
        str: UTC timestamp string.
    """

    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_clinic_list_payload() -> dict[str, Any]:
    """Load clinic list fixture JSON from disk.

    Args:
        None: Reads static clinic list fixture file.

    Returns:
        dict[str, Any]: Parsed clinic list JSON payload.
    """

    clinic_path = Path("data/clinic_list.json")
    if not clinic_path.exists():
        raise HTTPException(status_code=500, detail="Clinic list file is missing")
    return json.loads(clinic_path.read_text(encoding="utf-8"))


def _load_patient_resource(patient_id: str) -> dict[str, Any]:
    """Load patient resource for a patient id from local FHIR bundle fixture.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        dict[str, Any]: FHIR Patient resource from bundle fixture.
    """

    bundle_path = Path("data/fhir_bundles") / f"{patient_id}.json"
    if not bundle_path.exists():
        return {}
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Patient":
            return resource
    return {}


def _patient_from_records(clinic_row: dict[str, Any], patient_resource: dict[str, Any]) -> Patient:
    """Build a Patient schema object from clinic list and FHIR records.

    Args:
        clinic_row (dict[str, Any]): Patient row from `clinic_list.json`.
        patient_resource (dict[str, Any]): FHIR Patient resource dictionary.

    Returns:
        Patient: Normalised patient object for API responses.
    """

    nhs_number = ""
    for identifier in patient_resource.get("identifier", []):
        value = str(identifier.get("value", "")).strip()
        if value:
            nhs_number = value
            break

    date_of_birth = str(patient_resource.get("birthDate", ""))
    if date_of_birth and "-" in date_of_birth:
        yyyy, mm, dd = date_of_birth.split("-")
        date_of_birth = f"{dd}/{mm}/{yyyy}"

    return Patient(
        id=str(clinic_row.get("id", "")),
        nhs_number=nhs_number,
        name=str(clinic_row.get("name", "")),
        date_of_birth=date_of_birth,
        age=int(clinic_row.get("age", 0)),
        sex=str(clinic_row.get("sex", "")),
        appointment_time=str(clinic_row.get("time", "")),
        summary=str(clinic_row.get("summary", "")),
    )


def _get_patient(patient_id: str) -> Patient:
    """Resolve a patient from local fixture data.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        Patient: Patient record for the requested id.
    """

    payload = _load_clinic_list_payload()
    for row in payload.get("patients", []):
        if str(row.get("id")) == patient_id:
            resource = _load_patient_resource(patient_id)
            return _patient_from_records(row, resource)
    raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")


def _health_fhir_status() -> dict[str, Any]:
    """Compute lightweight FHIR service health metadata for health endpoint.

    Args:
        None: Reads settings and local data fixtures.

    Returns:
        dict[str, Any]: FHIR connectivity status and available patient count.
    """

    clinic_list_path = Path("data/clinic_list.json")
    if settings.USE_MOCK_FHIR and clinic_list_path.exists():
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

    gpu_info = orchestrator._medasr_model.model_manager.check_gpu()
    models = {
        "medasr": {
            "loaded": orchestrator._medasr_model.model_manager.get_model("medasr") is not None,
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


@app.get("/api/v1/patients")
def get_patients() -> dict[str, list[dict[str, Any]]]:
    """Return clinic patient list with normalised schema fields.

    Args:
        None: Reads local clinic list and FHIR bundle fixtures.

    Returns:
        dict[str, list[dict[str, Any]]]: Patient list payload.
    """

    payload = _load_clinic_list_payload()
    patients: list[dict[str, Any]] = []
    for row in payload.get("patients", []):
        patient_id = str(row.get("id", ""))
        if not patient_id:
            continue
        patient_model = _patient_from_records(row, _load_patient_resource(patient_id))
        patients.append(patient_model.model_dump())
    return {"patients": patients}


@app.get("/api/v1/patients/{patient_id}")
def get_patient(patient_id: str) -> dict[str, Any]:
    """Return a single patient by id.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        dict[str, Any]: Patient payload.
    """

    patient = _get_patient(patient_id)
    return patient.model_dump()


@app.post("/api/v1/patients/{patient_id}/context")
def generate_patient_context(patient_id: str) -> dict[str, Any]:
    """Generate patient context via EHR agent and return context JSON.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        dict[str, Any]: Structured patient context payload.
    """

    _get_patient(patient_id)
    context = orchestrator._ehr_agent.get_patient_context(patient_id)
    return context.model_dump(mode="json")


@app.post("/api/v1/consultations/start", status_code=201)
def start_consultation(payload: dict[str, str], background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Start a consultation session and trigger context prefetch in background.

    Args:
        payload (dict[str, str]): Request body containing patient_id.
        background_tasks (BackgroundTasks): FastAPI background task runner.

    Returns:
        dict[str, Any]: Consultation identifier and initial state.
    """

    patient_id = payload.get("patient_id", "")
    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")
    patient = _get_patient(patient_id)

    consultation = orchestrator.start_consultation(patient)
    background_tasks.add_task(orchestrator.prefetch_context, consultation.id)

    return {
        "consultation_id": consultation.id,
        "patient_id": patient_id,
        "status": ConsultationStatus.RECORDING.value,
        "started_at": consultation.started_at,
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

    try:
        consultation = orchestrator.get_consultation(consultation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    extension = Path(audio_file.filename or "").suffix.lower()
    if extension not in {".wav", ".webm"}:
        raise HTTPException(status_code=400, detail="Only WAV or WebM audio uploads are supported")

    uploads_root = Path("data/uploads") / consultation_id
    raw_path = uploads_root / f"raw{extension}"
    original_stem = Path(audio_file.filename or "audio").stem or "audio"
    wav_path = uploads_root / f"{original_stem}_16k.wav"

    try:
        _save_upload_temp(audio_file, raw_path)
        processed_path = raw_path if extension == ".wav" else Path(convert_to_wav_16k(str(raw_path), str(wav_path)))
        if extension == ".wav":
            processed_path = Path(convert_to_wav_16k(str(raw_path), str(wav_path)))

        audio_metadata = validate_audio(str(processed_path))
    except AudioError as exc:
        logger.error("Audio processing failed", consultation_id=consultation_id, error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    consultation.audio_file_path = str(processed_path)

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


@app.post("/api/v1/consultations/{consultation_id}/end", status_code=202)
def end_consultation(consultation_id: str) -> dict[str, Any]:
    """End a consultation and execute full processing pipeline.

    Args:
        consultation_id (str): Consultation identifier.

    Returns:
        dict[str, Any]: Pipeline kickoff and status metadata.
    """

    try:
        consultation = orchestrator.end_consultation(consultation_id)
        progress = orchestrator.get_progress(consultation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail={"error": "timeout", "message": str(exc)}) from exc
    except AudioError as exc:
        raise HTTPException(status_code=400, detail={"error": "audio_error", "message": str(exc)}) from exc
    except ModelExecutionError as exc:
        error_type = "audio_error" if "transcribed" in str(exc).lower() else "model_error"
        status_code = 400 if error_type == "audio_error" else 500
        raise HTTPException(status_code=status_code, detail={"error": error_type, "message": str(exc)}) from exc

    return {
        "consultation_id": consultation.id,
        "status": consultation.status.value,
        "pipeline_stage": progress.stage.value,
        "message": "Pipeline completed. Document is ready for review.",
    }


@app.get("/api/v1/consultations/{consultation_id}/transcript")
def get_transcript(consultation_id: str) -> dict[str, Any]:
    """Return transcript for a consultation when available.

    Args:
        consultation_id (str): Consultation identifier.

    Returns:
        dict[str, Any]: Transcript payload.
    """

    try:
        consultation = orchestrator.get_consultation(consultation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if consultation.transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not generated yet")
    return consultation.transcript.model_dump(mode="json")


@app.get("/api/v1/consultations/{consultation_id}/document")
def get_document(consultation_id: str) -> dict[str, Any]:
    """Return generated document placeholder for a consultation.

    Args:
        consultation_id (str): Consultation identifier.

    Returns:
        dict[str, Any]: Consultation document object or null.
    """

    try:
        consultation = orchestrator.get_consultation(consultation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "consultation_id": consultation_id,
        "document": consultation.document.model_dump(mode="json") if consultation.document else None,
    }


@app.get("/api/v1/consultations/{consultation_id}/progress")
def get_progress(consultation_id: str) -> dict[str, Any]:
    """Return latest pipeline progress object for a consultation.

    Args:
        consultation_id (str): Consultation identifier.

    Returns:
        dict[str, Any]: Pipeline progress payload.
    """

    try:
        progress = orchestrator.get_progress(consultation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return progress.model_dump(mode="json")


@app.post("/api/v1/consultations/{consultation_id}/document/sign-off")
def sign_off_document(consultation_id: str, payload: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    """Sign off a generated document and set consultation status to signed off.

    Args:
        consultation_id (str): Consultation identifier.

    Returns:
        dict[str, Any]: Signed-off document payload with updated status.
    """

    sections = (payload or {}).get("sections", [])

    try:
        if sections:
            orchestrator.update_document_sections(consultation_id, sections)
        document = orchestrator.sign_off_document(consultation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelExecutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "consultation_id": consultation_id,
        "status": ConsultationStatus.SIGNED_OFF.value,
        "document": document.model_dump(mode="json"),
    }


@app.post("/api/v1/consultations/{consultation_id}/document/regenerate-section")
def regenerate_document_section(
    consultation_id: str,
    payload: dict[str, str] = Body(...),
) -> dict[str, Any]:
    """Regenerate one document section while keeping other sections unchanged.

    Args:
        consultation_id (str): Consultation identifier.
        payload (dict[str, str]): Request body containing `section_heading`.

    Returns:
        dict[str, Any]: Updated document payload.
    """

    section_heading = payload.get("section_heading", "").strip()
    if not section_heading:
        raise HTTPException(status_code=400, detail="section_heading is required")

    try:
        document = orchestrator.regenerate_document_section(consultation_id, section_heading)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelExecutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "consultation_id": consultation_id,
        "status": ConsultationStatus.REVIEW.value,
        "document": document.model_dump(mode="json"),
    }
