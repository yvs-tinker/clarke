"""Tests for document generation evaluation metrics and report writing."""

from __future__ import annotations

from pathlib import Path

from evaluation.eval_doc_gen import (
    GeneratedLetterRecord,
    append_results_to_report,
    compute_bleu_rouge,
    fine_tuned_adapter_available,
    run_manual_review,
)


def test_compute_bleu_rouge_returns_high_scores_for_identical_text() -> None:
    """Ensure BLEU/ROUGE-L are strong when predictions match references exactly.

    Args:
        None: Uses in-memory letter fixtures.

    Returns:
        None: Asserts metric thresholds.
    """

    records = [
        GeneratedLetterRecord(
            index=0,
            transcript="A",
            generated_letter="History of presenting complaint\nPatient stable.",
            reference_letter="History of presenting complaint\nPatient stable.",
        ),
        GeneratedLetterRecord(
            index=1,
            transcript="B",
            generated_letter="Assessment and plan\nContinue treatment.",
            reference_letter="Assessment and plan\nContinue treatment.",
        ),
    ]

    bleu_score, rouge_l = compute_bleu_rouge(records)

    assert bleu_score >= 90.0
    assert rouge_l >= 0.99


def test_run_manual_review_reports_full_pass_for_well_structured_letters() -> None:
    """Validate manual-review proxy passes letters containing all required section headings.

    Args:
        None: Uses deterministic synthetic letters.

    Returns:
        None: Asserts 100% pass rates.
    """

    full_letter = (
        "History of presenting complaint\nSymptoms improved.\n"
        "Examination findings\nNo concerns.\n"
        "Investigation results\nBloods stable.\n"
        "Assessment and plan\nContinue management.\n"
        "Current medications\nMetformin."
    )

    records = [
        GeneratedLetterRecord(index=0, transcript="A", generated_letter=full_letter, reference_letter=full_letter),
        GeneratedLetterRecord(index=1, transcript="B", generated_letter=full_letter, reference_letter=full_letter),
    ]

    review_result = run_manual_review(records, review_sample_size=2)

    assert review_result.nhs_format_pass_rate == 1.0
    assert review_result.clinical_accuracy_pass_rate == 1.0


def test_append_results_to_report_writes_bleu_and_rouge_lines(tmp_path: Path) -> None:
    """Confirm markdown report appending includes BLEU and ROUGE-L markers.

    Args:
        tmp_path (Path): Temporary directory fixture from pytest.

    Returns:
        None: Asserts expected strings exist in report output.
    """

    report_path = tmp_path / "evaluation_report.md"
    append_results_to_report(
        report_path=report_path,
        test_sample_size=20,
        model_id="mock",
        bleu_score=12.34,
        rouge_l=0.456,
        manual_review=run_manual_review(
            [
                GeneratedLetterRecord(
                    index=0,
                    transcript="A",
                    generated_letter=(
                        "History of presenting complaint\nA\n"
                        "Examination findings\nB\n"
                        "Investigation results\nC\n"
                        "Assessment and plan\nD\n"
                        "Current medications\nE"
                    ),
                    reference_letter=(
                        "History of presenting complaint\nA\n"
                        "Examination findings\nB\n"
                        "Investigation results\nC\n"
                        "Assessment and plan\nD\n"
                        "Current medications\nE"
                    ),
                )
            ],
            review_sample_size=1,
        ),
        fine_tuned_available=False,
    )

    report_text = report_path.read_text(encoding="utf-8")
    assert "BLEU: 12.3400" in report_text
    assert "ROUGE-L: 0.4560" in report_text


def test_fine_tuned_adapter_available_ignores_readme(tmp_path: Path) -> None:
    """Ensure adapter availability requires artifacts beyond README documentation.

    Args:
        tmp_path (Path): Temporary directory fixture from pytest.

    Returns:
        None: Validates adapter detection behaviour.
    """

    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "README.md").write_text("info", encoding="utf-8")
    assert fine_tuned_adapter_available(adapter_dir) is False

    (adapter_dir / "adapter_config.json").write_text("{}", encoding="utf-8")
    assert fine_tuned_adapter_available(adapter_dir) is True
