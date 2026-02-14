"""End-to-end fusion tests for transcript + EHR context prompt assembly."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from backend.config import get_settings
from backend.models.ehr_agent import EHRAgent
from backend.models.medasr import MedASRModel

FHIR_SAMPLE_PATH = Path("data/fhir_bundles/pt-001.json")


async def _async_raw_context(patient_id: str) -> dict:
    """Return grouped raw FHIR context for async monkeypatching in EHRAgent tests.

    Args:
        patient_id (str): FHIR patient identifier used for context lookup.

    Returns:
        dict: Grouped FHIR resources keyed by the expected EHRAgent buckets.
    """

    bundle = json.loads(FHIR_SAMPLE_PATH.read_text(encoding="utf-8"))
    grouped = {
        "patient_id": patient_id,
        "patients": [],
        "conditions": [],
        "medications": [],
        "observations": [],
        "allergies": [],
        "diagnostic_reports": [],
        "encounters": [],
    }
    bucket_by_type = {
        "Patient": "patients",
        "Condition": "conditions",
        "MedicationRequest": "medications",
        "Observation": "observations",
        "AllergyIntolerance": "allergies",
        "DiagnosticReport": "diagnostic_reports",
        "Encounter": "encounters",
    }

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        bucket = bucket_by_type.get(resource.get("resourceType"))
        if bucket:
            grouped[bucket].append(resource)

    return grouped


def test_mrs_thompson_fusion(monkeypatch, capsys) -> None:
    """Verify transcript and FHIR context fuse into a rendered document-generation prompt.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture used to force deterministic mock model paths.
        capsys (pytest.CaptureFixture[str]): Fixture used to capture prompt console output.

    Returns:
        None: Assertions validate transcript details and key FHIR values in rendered prompt.
    """

    monkeypatch.setenv("MEDASR_MODEL_ID", "mock")
    get_settings.cache_clear()

    monkeypatch.setattr(
        "backend.models.ehr_agent.get_full_patient_context",
        (lambda patient_id: _async_raw_context(patient_id)),
    )

    medasr = MedASRModel()
    transcript = medasr.transcribe("data/demo/mrs_thompson.wav")

    ehr_agent = EHRAgent(model_id="mock")
    context = ehr_agent.get_patient_context("pt-001")

    env = Environment(loader=FileSystemLoader("backend/prompts"))
    template = env.get_template("document_generation.j2")
    context_json = json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2)
    rendered_prompt = template.render(
        letter_date="13 Feb 2026",
        clinician_name="Dr. Chen",
        clinician_title="Consultant",
        transcript=transcript.text,
        context_json=context_json,
    )

    print(rendered_prompt)
    printed = capsys.readouterr().out

    assert "HbA1c" in rendered_prompt
    assert "fatigue" in rendered_prompt.lower()
    assert "gliclazide" in rendered_prompt.lower()

    assert "55" in rendered_prompt and "mmol/mol" in rendered_prompt
    assert "eGFR" in rendered_prompt and "52" in rendered_prompt
    assert "Penicillin" in rendered_prompt

    assert printed.strip().startswith("<|system|>")

import math
import struct
import wave
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend import api
from backend.schemas import ClinicalDocument, ConsultationStatus, DocumentSection, PatientContext, Transcript


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


def _mock_context(patient_id: str) -> PatientContext:
    """Build deterministic mock PatientContext for pipeline hardening tests.

    Args:
        patient_id (str): Patient identifier used in context payload.

    Returns:
        PatientContext: Fully populated mock context object.
    """

    return PatientContext(
        patient_id=patient_id,
        demographics={"name": "Mrs. Margaret Thompson", "dob": "1958-03-14", "nhs_number": "943 476 5829"},
        problem_list=["Type 2 diabetes mellitus"],
        medications=[{"name": "Metformin", "dose": "1g", "frequency": "BD", "fhir_id": "med-1"}],
        allergies=[{"substance": "Penicillin", "reaction": "Anaphylaxis", "severity": "high"}],
        recent_labs=[],
        recent_imaging=[],
        clinical_flags=[],
        last_letter_excerpt=None,
        retrieval_warnings=[],
        retrieved_at=datetime.now(tz=timezone.utc).isoformat(),
    )


def _mock_document(consultation_id: str) -> ClinicalDocument:
    """Build deterministic mock ClinicalDocument for hardening-path assertions.

    Args:
        consultation_id (str): Consultation identifier used for document payload.

    Returns:
        ClinicalDocument: Mock generated document.
    """

    return ClinicalDocument(
        consultation_id=consultation_id,
        letter_date="2026-02-13",
        patient_name="Mrs. Margaret Thompson",
        patient_dob="14/03/1958",
        nhs_number="943 476 5829",
        addressee="Dr. Patel, Riverside Medical Centre",
        salutation="Dear Dr. Patel,",
        sections=[
            DocumentSection(heading="History Of Presenting Complaint", content="History", editable=True),
            DocumentSection(heading="Examination Findings", content="Exam", editable=True),
            DocumentSection(heading="Investigation Results", content="Investigations", editable=True),
            DocumentSection(heading="Assessment And Plan", content="Plan", editable=True),
        ],
        medications_list=["Metformin 1 g BD"],
        sign_off="Dr. S. Chen, Consultant Diabetologist",
        status=ConsultationStatus.REVIEW,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        generation_time_s=0.2,
        discrepancies=[],
    )


def _start_consultation_and_upload_audio(client: TestClient, tmp_path: Path) -> str:
    """Start a consultation and upload a valid WAV file.

    Args:
        client (TestClient): FastAPI test client.
        tmp_path (Path): Temporary path for generated audio.

    Returns:
        str: Consultation identifier.
    """

    start_response = client.post("/api/v1/consultations/start", json={"patient_id": "pt-001"})
    consultation_id = start_response.json()["consultation_id"]

    wav_path = _make_wav_file(tmp_path / f"{consultation_id}.wav")
    with wav_path.open("rb") as audio_stream:
        upload_response = client.post(
            f"/api/v1/consultations/{consultation_id}/audio",
            files={"audio_file": ("sample.wav", audio_stream, "audio/wav")},
            data={"is_final": "true"},
        )
    assert upload_response.status_code == 200
    return consultation_id


def test_pipeline_timeout(monkeypatch, tmp_path: Path) -> None:
    """Verify pipeline timeout is surfaced as a structured timeout response.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching pipeline behaviour.
        tmp_path (Path): Temporary path fixture.

    Returns:
        None: Assertions validate HTTP 504 timeout shape.
    """

    client = TestClient(api.app)
    consultation_id = _start_consultation_and_upload_audio(client, tmp_path)

    monkeypatch.setattr(api.orchestrator, "end_consultation", lambda _id: (_ for _ in ()).throw(TimeoutError("Pipeline timed out")))

    response = client.post(f"/api/v1/consultations/{consultation_id}/end")

    assert response.status_code == 504
    assert response.json()["detail"]["error"] == "timeout"


def test_fhir_failure_degradation(monkeypatch, tmp_path: Path) -> None:
    """Verify FHIR retrieval failures degrade to transcript-only generation.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for model patching.
        tmp_path (Path): Temporary path fixture.

    Returns:
        None: Assertions validate successful generation plus retrieval warning.
    """

    client = TestClient(api.app)

    monkeypatch.setattr(
        api.orchestrator._medasr_model,
        "transcribe",
        lambda _audio_path: Transcript(
            consultation_id="ignored",
            text="Transcript-only generation should still proceed.",
            duration_s=10.0,
            word_count=5,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        ),
    )
    monkeypatch.setattr(api.orchestrator._ehr_agent, "get_patient_context", lambda _patient_id: (_ for _ in ()).throw(RuntimeError("FHIR down")))

    captured_context: dict[str, PatientContext] = {}

    def _capture_document(transcript: str, context: PatientContext, max_new_tokens: int | None = None) -> ClinicalDocument:
        captured_context["ctx"] = context
        return _mock_document("placeholder")

    monkeypatch.setattr(api.orchestrator._doc_generator, "generate_document", _capture_document)

    consultation_id = _start_consultation_and_upload_audio(client, tmp_path)
    response = client.post(f"/api/v1/consultations/{consultation_id}/end")

    assert response.status_code == 202
    assert "ctx" in captured_context
    assert captured_context["ctx"].retrieval_warnings


def test_empty_audio(monkeypatch, tmp_path: Path) -> None:
    """Verify empty transcript is rejected with audio_error response.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for MedASR patching.
        tmp_path (Path): Temporary path fixture.

    Returns:
        None: Assertions validate error code and message.
    """

    client = TestClient(api.app)

    monkeypatch.setattr(
        api.orchestrator._medasr_model,
        "transcribe",
        lambda _audio_path: Transcript(
            consultation_id="ignored",
            text="   ",
            duration_s=10.0,
            word_count=0,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        ),
    )
    monkeypatch.setattr(api.orchestrator._ehr_agent, "get_patient_context", lambda patient_id: _mock_context(patient_id))
    monkeypatch.setattr(api.orchestrator._doc_generator, "generate_document", lambda transcript, context, max_new_tokens=None: _mock_document("placeholder"))

    consultation_id = _start_consultation_and_upload_audio(client, tmp_path)
    response = client.post(f"/api/v1/consultations/{consultation_id}/end")

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "audio_error"
    assert "could not be transcribed" in response.json()["detail"]["message"].lower()


def test_oversized_context_truncates_and_proceeds(monkeypatch, tmp_path: Path) -> None:
    """Verify oversized context is truncated and generation proceeds.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for model patching.
        tmp_path (Path): Temporary path fixture.

    Returns:
        None: Assertions validate successful completion and truncation warning.
    """

    client = TestClient(api.app)

    monkeypatch.setattr(
        api.orchestrator._medasr_model,
        "transcribe",
        lambda _audio_path: Transcript(
            consultation_id="ignored",
            text="Long consultation transcript.",
            duration_s=10.0,
            word_count=3,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        ),
    )

    huge_context = _mock_context("pt-001")
    huge_context.problem_list = [f"problem {idx}" for idx in range(8000)]
    monkeypatch.setattr(api.orchestrator._ehr_agent, "get_patient_context", lambda _patient_id: huge_context)

    captured_context: dict[str, PatientContext] = {}

    def _capture_document(transcript: str, context: PatientContext, max_new_tokens: int | None = None) -> ClinicalDocument:
        captured_context["ctx"] = context
        return _mock_document("placeholder")

    monkeypatch.setattr(api.orchestrator._doc_generator, "generate_document", _capture_document)

    consultation_id = _start_consultation_and_upload_audio(client, tmp_path)
    response = client.post(f"/api/v1/consultations/{consultation_id}/end")

    assert response.status_code == 202
    warnings = captured_context["ctx"].retrieval_warnings
    assert any("truncated" in warning.lower() for warning in warnings)
