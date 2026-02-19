"""Unit tests for LoRA fine-tuning data preparation and fallback configuration."""

from __future__ import annotations

import json
from pathlib import Path

from finetuning.train_lora import (
    build_attempt_sequence,
    build_dataset,
    format_training_example,
    load_training_records,
)


def test_load_training_records_reads_required_keys(tmp_path: Path) -> None:
    """Load JSONL records and keep required training keys.

    Args:
        tmp_path (Path): Pytest temporary directory fixture.

    Returns:
        None: Uses assertions for validation.
    """

    train_path = tmp_path / "train.jsonl"
    row = {
        "transcript": "Consultation text",
        "context": {"patient": "pt-001"},
        "reference_letter": "Reference letter text",
    }
    train_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    records = load_training_records(train_path)

    assert len(records) == 1
    assert records[0]["transcript"] == "Consultation text"


def test_format_training_example_renders_prompt_tokens() -> None:
    """Render transcript/context placeholders and append reference completion.

    Args:
        None: Uses inline sample data.

    Returns:
        None: Uses assertions for validation.
    """

    sample = {
        "transcript": "Patient reports fatigue",
        "context": {"hba1c": 55},
        "reference_letter": "Dear GP, follow-up arranged.",
    }
    template = "Transcript: {{ transcript }}\nContext: {{ context_json }}\nDate: {{ letter_date }}"

    output = format_training_example(sample, template)

    assert "Patient reports fatigue" in output
    assert '"hba1c": 55' in output
    assert "Dear GP, follow-up arranged." in output


def test_build_dataset_creates_text_column(tmp_path: Path) -> None:
    """Create Dataset object with expected text column for SFTTrainer.

    Args:
        tmp_path (Path): Pytest temporary directory fixture.

    Returns:
        None: Uses assertions for validation.
    """

    template_path = tmp_path / "document_generation.j2"
    template_path.write_text("{{ transcript }} :: {{ context_json }}", encoding="utf-8")
    samples = [
        {
            "transcript": "A",
            "context": {"foo": "bar"},
            "reference_letter": "B",
        }
    ]

    dataset = build_dataset(samples, template_path)

    assert len(dataset) == 1
    assert "text" in dataset.column_names


def test_build_attempt_sequence_contains_default_and_fallback() -> None:
    """Verify Task 28 fallback sequence order and values.

    Args:
        None: Uses function output only.

    Returns:
        None: Uses assertions for validation.
    """

    attempts = build_attempt_sequence()

    assert len(attempts) == 2
    assert attempts[0].lora_rank == 16
    assert attempts[1].lora_rank == 8
    assert attempts[1].sample_limit == 100
