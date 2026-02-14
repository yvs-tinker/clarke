"""Tests for Clarke FastAPI health, patient, and consultation pipeline endpoints."""

from __future__ import annotations

import math
import struct
import wave
from datetime import datetime, timezone
from pathlib import Path

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


def _mock_document(consultation_id: str, variant: str = "base") -> ClinicalDocument:
    """Build deterministic mock ClinicalDocument for API orchestration tests.

    Args:
        consultation_id (str): Consultation identifier used for document payload.
        variant (str): Text variant to support regenerate-section assertions.

    Returns:
        ClinicalDocument: Mock generated document with stable section headings.
    """

    suffix = "" if variant == "base" else f" ({variant})"
    return ClinicalDocument(
        consultation_id=consultation_id,
        letter_date="2026-02-13",
        patient_name="Mrs. Margaret Thompson",
        patient_dob="14/03/1958",
        nhs_number="943 476 5829",
        addressee="Dr. Patel, Riverside Medical Centre",
        salutation="Dear Dr. Patel,",
        sections=[
            DocumentSection(heading="History Of Presenting Complaint", content=f"History content{suffix}", editable=True),
            DocumentSection(heading="Examination Findings", content=f"Examination content{suffix}", editable=True),
            DocumentSection(heading="Investigation Results", content=f"Investigation content{suffix}", editable=True),
            DocumentSection(heading="Assessment And Plan", content=f"Plan content{suffix}", editable=True),
            DocumentSection(heading="Current Medications", content=f"Medication content{suffix}", editable=True),
        ],
        medications_list=["Metformin 1 g BD", "Gliclazide 40 mg OD"],
        sign_off="Dr. S. Chen, Consultant Diabetologist",
        status=ConsultationStatus.REVIEW,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        generation_time_s=0.42,
        discrepancies=[],
    )


def _mock_context(patient_id: str) -> PatientContext:
    """Build deterministic mock PatientContext for API orchestration tests.

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


def test_patients_endpoints_return_clinic_records() -> None:
    """Verify patient list and single-patient endpoints return expected records.

    Args:
        None: Calls patient endpoints with a FastAPI test client.

    Returns:
        None: Assertions validate schema and selected patient id.
    """

    client = TestClient(api.app)

    list_response = client.get("/api/v1/patients")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert "patients" in list_payload
    assert any(patient["id"] == "pt-001" for patient in list_payload["patients"])

    patient_response = client.get("/api/v1/patients/pt-001")
    assert patient_response.status_code == 200
    assert patient_response.json()["id"] == "pt-001"


def test_consultation_flow_start_audio_end_and_progress(monkeypatch, tmp_path: Path) -> None:
    """Verify start→audio→end pipeline flow and progress endpoint transitions.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for replacing model calls with deterministic mocks.
        tmp_path (Path): Temporary path used to generate test WAV file.

    Returns:
        None: Assertions validate consultation lifecycle endpoints.
    """

    client = TestClient(api.app)

    monkeypatch.setattr(api.orchestrator._ehr_agent, "get_patient_context", lambda patient_id: _mock_context(patient_id))

    def _mock_transcribe(audio_path: str) -> Transcript:
        return Transcript(
            consultation_id="ignored",
            text="Patient reports fatigue; HbA1c reviewed and gliclazide discussed.",
            duration_s=62.5,
            word_count=9,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    monkeypatch.setattr(api.orchestrator._medasr_model, "transcribe", _mock_transcribe)
    monkeypatch.setattr(
        api.orchestrator._doc_generator,
        "generate_document",
        lambda transcript, context: _mock_document("placeholder", "base"),
    )

    start_response = client.post("/api/v1/consultations/start", json={"patient_id": "pt-001"})
    assert start_response.status_code == 201
    consultation_id = start_response.json()["consultation_id"]

    wav_path = _make_wav_file(tmp_path / "sample.wav")
    with wav_path.open("rb") as audio_stream:
        upload_response = client.post(
            f"/api/v1/consultations/{consultation_id}/audio",
            files={"audio_file": ("sample.wav", audio_stream, "audio/wav")},
            data={"is_final": "true"},
        )
    assert upload_response.status_code == 200

    end_response = client.post(f"/api/v1/consultations/{consultation_id}/end")
    assert end_response.status_code == 202
    assert end_response.json()["pipeline_stage"] == "complete"
    assert end_response.json()["status"] == "review"

    progress_response = client.get(f"/api/v1/consultations/{consultation_id}/progress")
    assert progress_response.status_code == 200
    progress_payload = progress_response.json()
    assert progress_payload["stage"] == "complete"
    assert progress_payload["progress_pct"] == 100

    transcript_response = client.get(f"/api/v1/consultations/{consultation_id}/transcript")
    assert transcript_response.status_code == 200
    assert "fatigue" in transcript_response.json()["text"].lower()

    document_response = client.get(f"/api/v1/consultations/{consultation_id}/document")
    assert document_response.status_code == 200
    document_payload = document_response.json()["document"]
    assert document_payload is not None
    assert len(document_payload["sections"]) >= 4


def test_context_endpoint_returns_patient_context(monkeypatch) -> None:
    """Verify context endpoint returns EHR agent result for existing patient.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for deterministic EHR context mock.

    Returns:
        None: Assertions validate context fields from endpoint response.
    """

    client = TestClient(api.app)
    monkeypatch.setattr(api.orchestrator._ehr_agent, "get_patient_context", lambda patient_id: _mock_context(patient_id))

    response = client.post("/api/v1/patients/pt-001/context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == "pt-001"
    assert any("penicillin" in allergy["substance"].lower() for allergy in payload["allergies"])


def test_document_sign_off_and_regenerate_section(monkeypatch, tmp_path: Path) -> None:
    """Verify document sign-off and per-section regeneration endpoints update consultation state.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for replacing model calls with deterministic mocks.
        tmp_path (Path): Temporary path used to generate WAV input for consultation flow.

    Returns:
        None: Assertions validate signed-off status and regenerated section content.
    """

    client = TestClient(api.app)

    monkeypatch.setattr(api.orchestrator._ehr_agent, "get_patient_context", lambda patient_id: _mock_context(patient_id))

    def _mock_transcribe(audio_path: str) -> Transcript:
        return Transcript(
            consultation_id="ignored",
            text="Follow-up consultation transcript for document actions.",
            duration_s=45.0,
            word_count=6,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    regenerate_state = {"count": 0}

    def _mock_generate_document(transcript: str, context: PatientContext) -> ClinicalDocument:
        regenerate_state["count"] += 1
        variant = "base" if regenerate_state["count"] == 1 else "regen"
        return _mock_document("placeholder", variant)

    monkeypatch.setattr(api.orchestrator._medasr_model, "transcribe", _mock_transcribe)
    monkeypatch.setattr(api.orchestrator._doc_generator, "generate_document", _mock_generate_document)

    start_response = client.post("/api/v1/consultations/start", json={"patient_id": "pt-001"})
    assert start_response.status_code == 201
    consultation_id = start_response.json()["consultation_id"]

    wav_path = _make_wav_file(tmp_path / "sample_actions.wav")
    with wav_path.open("rb") as audio_stream:
        upload_response = client.post(
            f"/api/v1/consultations/{consultation_id}/audio",
            files={"audio_file": ("sample_actions.wav", audio_stream, "audio/wav")},
            data={"is_final": "true"},
        )
    assert upload_response.status_code == 200

    end_response = client.post(f"/api/v1/consultations/{consultation_id}/end")
    assert end_response.status_code == 202

    sign_off_response = client.post(f"/api/v1/consultations/{consultation_id}/document/sign-off")
    assert sign_off_response.status_code == 200
    sign_off_payload = sign_off_response.json()
    assert sign_off_payload["status"] == "signed_off"
    assert sign_off_payload["document"]["status"] == "signed_off"

    regenerate_response = client.post(
        f"/api/v1/consultations/{consultation_id}/document/regenerate-section",
        json={"section_heading": "Investigation Results"},
    )
    assert regenerate_response.status_code == 200
    regenerate_payload = regenerate_response.json()
    assert regenerate_payload["status"] == "review"

    updated_section = next(
        section
        for section in regenerate_payload["document"]["sections"]
        if section["heading"].lower() == "investigation results"
    )
    assert "regen" in updated_section["content"].lower()
