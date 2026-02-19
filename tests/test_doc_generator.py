"""Tests for MedGemma 27B document generator prompt flow and output parsing."""

from __future__ import annotations

import json
from pathlib import Path

from backend.models.doc_generator import DocumentGenerator
from backend.models.ehr_agent import EHRAgent

FHIR_SAMPLE_PATH = Path("data/fhir_bundles/pt-001.json")


async def _async_raw_context(patient_id: str) -> dict:
    """Return grouped raw context for async monkeypatching in doc generator tests.

    Args:
        patient_id (str): Patient identifier used in context payload.

    Returns:
        dict: Grouped FHIR resources payload.
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
    type_mapping = {
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
        bucket = type_mapping.get(resource.get("resourceType"))
        if bucket:
            grouped[bucket].append(resource)
    return grouped


def test_parse_sections_extracts_known_headings() -> None:
    """Verify section parser extracts heading blocks from generated letter text.

    Args:
        None: Uses deterministic text fixture.

    Returns:
        None: Assertions validate heading and content extraction.
    """

    sample_letter = (
        "History of presenting complaint\n"
        "Symptoms discussed.\n"
        "Examination findings\n"
        "No acute concerns.\n"
        "Investigation results\n"
        "HbA1c 55 mmol/mol.\n"
        "Assessment and plan\n"
        "Follow-up in three months.\n"
        "Current medications\n"
        "Metformin."
    )

    sections = DocumentGenerator._parse_sections(sample_letter)

    assert len(sections) >= 4
    assert sections[0].heading == "History Of Presenting Complaint"
    assert "Symptoms" in sections[0].content


def test_generate_document_mock_mode_returns_clinical_document(monkeypatch) -> None:
    """Verify mock mode generation yields valid ClinicalDocument with expected sections.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for deterministic FHIR context stubbing.

    Returns:
        None: Assertions validate ClinicalDocument structure and section count.
    """

    monkeypatch.setattr(
        "backend.models.ehr_agent.get_full_patient_context",
        (lambda patient_id: _async_raw_context(patient_id)),
    )

    context = EHRAgent(model_id="mock").get_patient_context("pt-001")
    generator = DocumentGenerator(model_id="mock")

    document = generator.generate_document(
        transcript="Patient reports fatigue and challenges taking gliclazide consistently.",
        context=context,
    )

    assert document.consultation_id == "pt-001"
    assert len(document.sections) >= 4
    assert any("Investigation" in section.heading for section in document.sections)
    assert any("Metformin" in med for med in document.medications_list)
