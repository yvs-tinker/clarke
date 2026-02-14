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
