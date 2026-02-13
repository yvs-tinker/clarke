"""Clarke data models — Pydantic v2 schemas for all system objects."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConsultationStatus(str, Enum):
    """Status lifecycle for a consultation session."""

    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    PROCESSING = "processing"
    REVIEW = "review"
    SIGNED_OFF = "signed_off"


class PipelineStage(str, Enum):
    """Discrete execution stages for the consultation pipeline."""

    TRANSCRIBING = "transcribing"
    RETRIEVING_CONTEXT = "retrieving_context"
    GENERATING_DOCUMENT = "generating_document"
    COMPLETE = "complete"
    FAILED = "failed"


class Patient(BaseModel):
    """A patient in the clinic list."""

    id: str = Field(description="FHIR Patient resource ID")
    nhs_number: str = Field(description="NHS number (format: XXX XXX XXXX)")
    name: str = Field(description="Full name (e.g., 'Mrs. Margaret Thompson')")
    date_of_birth: str = Field(description="DOB in DD/MM/YYYY format")
    age: int
    sex: str = Field(description="'Male' or 'Female'")
    appointment_time: str = Field(description="HH:MM format")
    summary: str = Field(description="One-line clinical summary for dashboard card")


class LabResult(BaseModel):
    """A single laboratory result with trend."""

    name: str = Field(description="e.g., 'HbA1c'")
    value: str = Field(description="e.g., '55'")
    unit: str = Field(description="e.g., 'mmol/mol'")
    reference_range: Optional[str] = Field(default=None, description="e.g., '20-42'")
    date: str = Field(description="ISO date of result")
    trend: Optional[str] = Field(default=None, description="'rising', 'falling', 'stable', or None")
    previous_value: Optional[str] = Field(default=None, description="Previous result value")
    previous_date: Optional[str] = Field(default=None)
    fhir_resource_id: Optional[str] = Field(default=None, description="Source FHIR Observation ID")


class PatientContext(BaseModel):
    """Structured patient context synthesised by the EHR Agent from FHIR data."""

    patient_id: str
    demographics: dict = Field(description="name, dob, nhs_number, age, sex, address")
    problem_list: list[str] = Field(description="Active diagnoses, e.g., ['Type 2 Diabetes Mellitus (2019)', ...]")
    medications: list[dict] = Field(
        description="[{'name': 'Metformin', 'dose': '1g', 'frequency': 'BD', 'fhir_id': '...'}]"
    )
    allergies: list[dict] = Field(
        description="[{'substance': 'Penicillin', 'reaction': 'Anaphylaxis', 'severity': 'high'}]"
    )
    recent_labs: list[LabResult] = Field(default_factory=list)
    recent_imaging: list[dict] = Field(default_factory=list, description="[{'type': 'CXR', 'date': '...', 'summary': '...'}]")
    clinical_flags: list[str] = Field(default_factory=list, description="['HbA1c rising trend over 6 months']")
    last_letter_excerpt: Optional[str] = Field(default=None, description="Key excerpt from most recent clinic letter")
    retrieval_warnings: list[str] = Field(default_factory=list, description="Warnings if some FHIR queries failed")
    retrieved_at: str = Field(description="ISO timestamp of retrieval")


class Transcript(BaseModel):
    """Consultation transcript produced by MedASR."""

    consultation_id: str
    text: str = Field(description="Full transcript text")
    duration_s: float = Field(description="Audio duration in seconds")
    word_count: int
    created_at: str


class DocumentSection(BaseModel):
    """A single section of the generated clinical letter."""

    heading: str = Field(description="e.g., 'History of presenting complaint'")
    content: str = Field(description="Section body text")
    editable: bool = Field(default=True)
    fhir_sources: list[str] = Field(default_factory=list, description="FHIR resource IDs cited in this section")


class ClinicalDocument(BaseModel):
    """A generated NHS clinical letter."""

    consultation_id: str
    letter_date: str
    patient_name: str
    patient_dob: str
    nhs_number: str
    addressee: str = Field(description="GP name and address")
    salutation: str = Field(description="e.g., 'Dear Dr. Patel,'")
    sections: list[DocumentSection]
    medications_list: list[str] = Field(description="Current medications (formatted)")
    sign_off: str = Field(description="e.g., 'Dr. S. Chen, Consultant Diabetologist'")
    status: ConsultationStatus = ConsultationStatus.REVIEW
    generated_at: str
    generation_time_s: float = Field(description="Time taken for MedGemma 27B inference")
    discrepancies: list[dict] = Field(default_factory=list, description="[{'type': 'allergy_mismatch', 'detail': '...'}]")


class Consultation(BaseModel):
    """A complete consultation session — links patient, transcript, context, and document."""

    id: str = Field(description="Unique consultation ID (UUID)")
    patient: Patient
    status: ConsultationStatus = ConsultationStatus.IDLE
    pipeline_stage: Optional[PipelineStage] = None
    context: Optional[PatientContext] = None
    transcript: Optional[Transcript] = None
    document: Optional[ClinicalDocument] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    audio_file_path: Optional[str] = None


class PipelineProgress(BaseModel):
    """Real-time pipeline progress updates pushed to the UI."""

    consultation_id: str
    stage: PipelineStage
    progress_pct: int = Field(ge=0, le=100)
    message: str = Field(description="Human-readable status, e.g., 'Finalising transcript...'")


class ErrorResponse(BaseModel):
    """Standardised error response format."""

    error: str = Field(description="Error category: 'model_error', 'fhir_error', 'audio_error', 'timeout'")
    message: str = Field(description="Human-readable error message for UI display")
    detail: Optional[str] = Field(default=None, description="Technical detail (logged, not shown to user)")
    consultation_id: Optional[str] = None
    timestamp: str
