"""Tests for synthetic training data generation."""

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "finetuning" / "generate_training_data.py"
SPEC = importlib.util.spec_from_file_location("generate_training_data", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_generate_triplets_has_required_schema() -> None:
    """Ensure generated records include required fields and minimum transcript length."""

    records = MODULE.generate_triplets(total_samples=5, seed=7)
    assert len(records) == 5

    for record in records:
        assert {"transcript", "context", "reference_letter"}.issubset(record.keys())
        assert len(record["transcript"].split()) >= 150
        assert "patient_id" in record["context"]


def test_write_jsonl_and_quality_review(tmp_path: Path) -> None:
    """Verify JSONL writing and sampling-based quality review pass for valid records."""

    records = MODULE.generate_triplets(total_samples=10, seed=11)
    destination = tmp_path / "train.jsonl"
    MODULE.write_jsonl(records, destination)

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10
    for line in lines:
        parsed = json.loads(line)
        assert "reference_letter" in parsed

    passed, failures = MODULE.review_quality(records, sample_size=5, seed=13)
    assert passed is True
    assert failures == []
