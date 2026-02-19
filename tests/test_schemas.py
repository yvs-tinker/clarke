"""Validation tests for Clarke Pydantic schemas."""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from backend.schemas import (
    ClinicalDocument,
    Consultation,
    ConsultationStatus,
    DocumentSection,
    ErrorResponse,
    LabResult,
    Patient,
    PatientContext,
    PipelineProgress,
    PipelineStage,
    Transcript,
)


def valid_patient_data() -> dict:
    """Return valid fixture data for a Patient model instance."""
    return {
        "id": "pt-001",
        "nhs_number": "123 456 7890",
        "name": "Mrs. Margaret Thompson",
        "date_of_birth": "01/02/1959",
        "age": 67,
        "sex": "Female",
        "appointment_time": "09:30",
        "summary": "T2DM follow-up with rising HbA1c",
    }


def valid_lab_result_data() -> dict:
    """Return valid fixture data for a LabResult model instance."""
    return {
        "name": "HbA1c",
        "value": "55",
        "unit": "mmol/mol",
        "reference_range": "20-42",
        "date": "2026-02-01",
        "trend": "rising",
        "previous_value": "48",
        "previous_date": "2025-11-01",
        "fhir_resource_id": "obs-123",
    }


def valid_patient_context_data() -> dict:
    """Return valid fixture data for a PatientContext model instance."""
    return {
        "patient_id": "pt-001",
        "demographics": {
            "name": "Mrs. Margaret Thompson",
            "dob": "01/02/1959",
            "nhs_number": "123 456 7890",
            "age": 67,
            "sex": "Female",
            "address": "1 Clinic Road",
        },
        "problem_list": ["Type 2 Diabetes Mellitus (2019)", "Hypertension"],
        "medications": [{"name": "Metformin", "dose": "1g", "frequency": "BD", "fhir_id": "med-1"}],
        "allergies": [{"substance": "Penicillin", "reaction": "Anaphylaxis", "severity": "high"}],
        "recent_labs": [valid_lab_result_data()],
        "recent_imaging": [{"type": "CXR", "date": "2026-01-15", "summary": "No acute findings"}],
        "clinical_flags": ["HbA1c rising trend over 6 months"],
        "last_letter_excerpt": "Continue current regimen and repeat labs in 3 months.",
        "retrieval_warnings": [],
        "retrieved_at": "2026-02-13T09:00:00Z",
    }


def valid_transcript_data() -> dict:
    """Return valid fixture data for a Transcript model instance."""
    return {
        "consultation_id": "cons-001",
        "text": "Patient reports higher home glucose readings.",
        "duration_s": 58.7,
        "word_count": 120,
        "created_at": "2026-02-13T09:05:00Z",
    }


def valid_document_section_data() -> dict:
    """Return valid fixture data for a DocumentSection model instance."""
    return {
        "heading": "Assessment",
        "content": "Glycaemic control has worsened compared with prior review.",
        "editable": True,
        "fhir_sources": ["obs-123", "cond-200"],
    }


def valid_clinical_document_data() -> dict:
    """Return valid fixture data for a ClinicalDocument model instance."""
    return {
        "consultation_id": "cons-001",
        "letter_date": "2026-02-13",
        "patient_name": "Mrs. Margaret Thompson",
        "patient_dob": "01/02/1959",
        "nhs_number": "123 456 7890",
        "addressee": "Dr. Patel, Clarke Medical Practice",
        "salutation": "Dear Dr. Patel,",
        "sections": [valid_document_section_data()],
        "medications_list": ["Metformin 1g BD", "Gliclazide 40mg OD"],
        "sign_off": "Dr. S. Chen, Consultant Diabetologist",
        "status": ConsultationStatus.REVIEW,
        "generated_at": "2026-02-13T09:06:00Z",
        "generation_time_s": 14.2,
        "discrepancies": [],
    }


def valid_consultation_data() -> dict:
    """Return valid fixture data for a Consultation model instance."""
    return {
        "id": "cons-001",
        "patient": valid_patient_data(),
        "status": ConsultationStatus.PROCESSING,
        "pipeline_stage": PipelineStage.GENERATING_DOCUMENT,
        "context": valid_patient_context_data(),
        "transcript": valid_transcript_data(),
        "document": valid_clinical_document_data(),
        "started_at": "2026-02-13T09:00:00Z",
        "ended_at": "2026-02-13T09:07:00Z",
        "audio_file_path": "data/demo/mrs_thompson.wav",
    }


def test_enums_have_expected_values() -> None:
    """Ensure enum values exactly match the technical specification."""
    assert [status.value for status in ConsultationStatus] == [
        "idle",
        "recording",
        "paused",
        "processing",
        "review",
        "signed_off",
    ]
    assert [stage.value for stage in PipelineStage] == [
        "transcribing",
        "retrieving_context",
        "generating_document",
        "complete",
        "failed",
    ]


@pytest.mark.parametrize(
    "model_cls,payload",
    [
        (Patient, valid_patient_data()),
        (LabResult, valid_lab_result_data()),
        (PatientContext, valid_patient_context_data()),
        (Transcript, valid_transcript_data()),
        (DocumentSection, valid_document_section_data()),
        (ClinicalDocument, valid_clinical_document_data()),
        (Consultation, valid_consultation_data()),
        (
            PipelineProgress,
            {
                "consultation_id": "cons-001",
                "stage": PipelineStage.TRANSCRIBING,
                "progress_pct": 40,
                "message": "Transcribing audio...",
            },
        ),
        (
            ErrorResponse,
            {
                "error": "timeout",
                "message": "Pipeline exceeded timeout window.",
                "detail": "operation exceeded 120s",
                "consultation_id": "cons-001",
                "timestamp": "2026-02-13T09:08:00Z",
            },
        ),
    ],
)
def test_models_validate_with_valid_data(model_cls: type, payload: dict) -> None:
    """Confirm each schema accepts a representative valid payload."""
    instance = model_cls.model_validate(payload)
    assert instance is not None


@pytest.mark.parametrize(
    "model_cls,payload",
    [
        (Patient, {**valid_patient_data(), "age": "sixty-seven"}),
        (Patient, {k: v for k, v in valid_patient_data().items() if k != "id"}),
        (LabResult, {**valid_lab_result_data(), "date": 20260201}),
        (PatientContext, {**valid_patient_context_data(), "problem_list": "diabetes"}),
        (Transcript, {**valid_transcript_data(), "duration_s": [58.7]}),
        (DocumentSection, {**valid_document_section_data(), "editable": {"value": True}}),
        (ClinicalDocument, {**valid_clinical_document_data(), "sections": "Assessment text"}),
        (Consultation, {**valid_consultation_data(), "pipeline_stage": "bad_stage"}),
        (
            PipelineProgress,
            {
                "consultation_id": "cons-001",
                "stage": PipelineStage.TRANSCRIBING,
                "progress_pct": 120,
                "message": "Out of bounds",
            },
        ),
        (
            ErrorResponse,
            {
                "message": "Missing error field",
                "timestamp": "2026-02-13T09:08:00Z",
            },
        ),
    ],
)
def test_models_reject_invalid_data(model_cls: type, payload: dict) -> None:
    """Ensure schemas reject payloads with invalid types or missing required fields."""
    with pytest.raises(ValidationError):
        model_cls.model_validate(payload)
