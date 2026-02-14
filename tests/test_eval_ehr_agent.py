"""Tests for EHR fact recall evaluation logic (Task 30)."""

from __future__ import annotations

from pathlib import Path

from backend.models.ehr_agent import EHRAgent
from evaluation.eval_ehr_agent import (
    DEMO_PATIENT_IDS,
    build_raw_context_from_bundle,
    evaluate_all_patients,
    evaluate_patient,
    extract_context_facts,
    load_gold_facts,
)


def test_gold_standard_files_exist_for_all_demo_patients() -> None:
    """Validate all expected gold-standard files are present and non-empty.

    Args:
        None: Test function consumes static project paths.

    Returns:
        None: Asserts required files exist.
    """

    gold_dir = Path("evaluation/gold_standards")
    for patient_id in DEMO_PATIENT_IDS:
        facts = load_gold_facts(patient_id=patient_id, gold_dir=gold_dir)
        assert facts, f"Gold facts missing for {patient_id}"


def test_patient_metrics_are_bounded_for_pt001() -> None:
    """Ensure per-patient metrics stay in valid [0,1] range.

    Args:
        None: Test uses fixed directories and patient id.

    Returns:
        None: Asserts metric bounds and non-zero fact counts.
    """

    result = evaluate_patient(
        patient_id="pt-001",
        gold_dir=Path("evaluation/gold_standards"),
        bundle_dir=Path("data/fhir_bundles"),
        agent=EHRAgent(model_id="mock"),
    )

    assert 0.0 <= result.recall <= 1.0
    assert 0.0 <= result.precision <= 1.0
    assert 0.0 <= result.hallucination_rate <= 1.0
    assert result.gold_count > 0
    assert result.output_count > 0


def test_aggregate_metrics_computed_for_all_patients() -> None:
    """Verify Task 30 evaluator computes metrics for all 5 demo patients.

    Args:
        None: Test uses default project directories.

    Returns:
        None: Asserts patient count and aggregate ranges.
    """

    patient_results, aggregate = evaluate_all_patients(
        gold_dir=Path("evaluation/gold_standards"),
        bundle_dir=Path("data/fhir_bundles"),
    )

    assert len(patient_results) == 5
    assert all(result.patient_id in DEMO_PATIENT_IDS for result in patient_results)
    assert 0.0 <= aggregate.recall <= 1.0
    assert 0.0 <= aggregate.precision <= 1.0
    assert 0.0 <= aggregate.hallucination_rate <= 1.0


def test_extract_context_facts_returns_key_fact_types() -> None:
    """Confirm extractor emits demographic and clinical fact prefixes.

    Args:
        None: Test evaluates first demo patient context output.

    Returns:
        None: Asserts fact categories are represented.
    """

    patient_id = "pt-001"
    raw_context = build_raw_context_from_bundle(
        patient_id=patient_id,
        bundle_path=Path("data/fhir_bundles") / f"{patient_id}.json",
    )
    context = EHRAgent(model_id="mock")._build_context_from_raw(raw_context)
    facts = extract_context_facts(context)

    assert any(fact.startswith("name:") for fact in facts)
    assert any(fact.startswith("problem:") for fact in facts)
    assert any(fact.startswith("medication:") for fact in facts)
