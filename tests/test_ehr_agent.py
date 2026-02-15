"""Tests for EHRAgent parsing and deterministic context fallback behaviour."""

from __future__ import annotations

import json
from pathlib import Path

from backend.models.ehr_agent import EHRAgent, parse_agent_output


FHIR_SAMPLE_PATH = Path("data/fhir_bundles/pt-001.json")


async def _async_raw_context(patient_id: str) -> dict:
    """Return async raw context helper for monkeypatched query call.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        dict: Raw grouped FHIR context payload.
    """

    return _build_raw_context(patient_id)


def _build_raw_context(patient_id: str) -> dict:
    """Build deterministic raw context payload from local FHIR bundle fixture.

    Args:
        patient_id (str): Patient identifier used to construct context.

    Returns:
        dict: Aggregated resources grouped by FHIR type.
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


def test_parse_agent_output_strips_system_and_markdown_fences() -> None:
    """Verify parser extracts first valid JSON object from noisy model output.

    Args:
        None: Uses hardcoded sample output with prompt leakage and code fences.

    Returns:
        None: Assertions validate parser output fields.
    """

    raw = (
        "<|system|>hidden instructions<|end|>\n"
        "```json\n"
        '{"patient_id": "pt-001", "problem_list": ["Type 2 diabetes mellitus"]}'
        "\n```"
    )

    payload = parse_agent_output(raw)

    assert payload["patient_id"] == "pt-001"
    assert payload["problem_list"] == ["Type 2 diabetes mellitus"]


def test_ehr_agent_mock_mode_returns_valid_patient_context_for_pt001(monkeypatch) -> None:
    """Verify mock mode returns deterministic PatientContext populated from FHIR data.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture used to patch raw context retrieval.

    Returns:
        None: Assertions verify key context fields for pt-001 fixtures.
    """

    monkeypatch.setattr(
        "backend.models.ehr_agent.get_full_patient_context",
        (lambda patient_id: _async_raw_context(patient_id)),
    )

    agent = EHRAgent(model_id="mock")
    context = agent.get_patient_context("pt-001")

    assert context.patient_id == "pt-001"
    assert any("diabetes" in problem.lower() for problem in context.problem_list)
    assert any("metformin" in medication["name"].lower() for medication in context.medications)
    assert any("penicillin" in allergy["substance"].lower() for allergy in context.allergies)
    assert any(lab.name == "HbA1c" and lab.value == "55" for lab in context.recent_labs)


def test_ehr_agent_fallback_path_sets_warning_when_summarisation_fails(monkeypatch) -> None:
    """Verify retrieval warnings are added when model summarisation path fails twice.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for forcing repeated summarisation failures.

    Returns:
        None: Assertions verify deterministic fallback and warning propagation.
    """

    monkeypatch.setattr(
        "backend.models.ehr_agent.get_full_patient_context",
        (lambda patient_id: _async_raw_context(patient_id)),
    )

    agent = EHRAgent(model_id="mock")
    agent.is_mock_mode = False

    monkeypatch.setattr(agent, "load_model", lambda: None)

    def always_fail(_: dict) -> dict:
        raise ValueError("invalid model output")

    monkeypatch.setattr(agent, "_summarise_with_model", always_fail)

    context = agent.get_patient_context("pt-001")

    assert context.retrieval_warnings
    assert "deterministic extraction" in context.retrieval_warnings[0].lower()
    assert context.patient_id == "pt-001"
