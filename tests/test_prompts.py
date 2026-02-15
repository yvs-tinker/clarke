"""Tests for Jinja2 prompt templates used by EHR synthesis and document generation."""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader


def test_document_generation_template_renders_required_sections() -> None:
    """Render document template and assert key instruction and payload fields are present.

    Args:
        None: Test constructs a Jinja2 environment directly from prompt directory.

    Returns:
        None: Assertions validate rendered output content.
    """

    env = Environment(loader=FileSystemLoader("backend/prompts"))
    template = env.get_template("document_generation.j2")
    rendered = template.render(
        letter_date="13 Feb 2026",
        clinician_name="Dr. Chen",
        clinician_title="Consultant",
        transcript="HbA1c discussed with fatigue and thirst symptoms.",
        context_json='{"recent_labs": [{"test": "HbA1c", "value": 55}]}',
    )

    assert "NHS clinical documentation assistant" in rendered
    assert "HbA1c discussed with fatigue and thirst symptoms." in rendered
    assert '"value": 55' in rendered


def test_context_synthesis_template_includes_required_inputs() -> None:
    """Render context synthesis template and assert patient and raw FHIR fields are injected.

    Args:
        None: Test renders template with simple payload placeholders.

    Returns:
        None: Assertions validate required variable interpolation.
    """

    env = Environment(loader=FileSystemLoader("backend/prompts"))
    template = env.get_template("context_synthesis.j2")
    rendered = template.render(patient_id="pt-001", raw_fhir_data='{"resourceType": "Bundle"}')

    assert "PATIENT ID: pt-001" in rendered
    assert 'RAW FHIR DATA:\n{"resourceType": "Bundle"}' in rendered
