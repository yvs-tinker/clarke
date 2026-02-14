"""Tests for MedASR WER evaluation helpers and report output."""

from __future__ import annotations

from pathlib import Path

from evaluation.eval_medasr import (
    WerResult,
    append_results_to_report,
    calculate_wer,
    run_medasr_evaluation,
)


def test_calculate_wer_zero_for_identical_text() -> None:
    """Verify WER returns zero when reference and hypothesis are identical.

    Args:
        None: Pure function test with fixed strings.

    Returns:
        None: Asserts score is exactly zero.
    """

    assert calculate_wer("the quick brown fox", "the quick brown fox") == 0.0


def test_run_medasr_evaluation_returns_three_demo_results() -> None:
    """Verify evaluation computes WER values for all configured demo clips.

    Args:
        None: Uses repository demo fixtures.

    Returns:
        None: Asserts expected clip coverage and model selection.
    """

    results, model_id = run_medasr_evaluation(force_mock=True)

    assert len(results) == 3
    assert model_id == "mock"
    assert {item.clip_name for item in results} == {"mrs_thompson", "mr_okafor", "ms_patel"}


def test_append_results_to_report_writes_medasr_markers(tmp_path: Path) -> None:
    """Verify markdown report writer appends required MedASR WER markers.

    Args:
        tmp_path (Path): Temporary directory fixture.

    Returns:
        None: Asserts report text contains Task 29 output lines.
    """

    report_path = tmp_path / "evaluation_report.md"
    results = [
        WerResult("mrs_thompson", 100, 100, 0.0),
        WerResult("mr_okafor", 100, 95, 0.1),
        WerResult("ms_patel", 100, 98, 0.2),
    ]

    append_results_to_report(results=results, report_path=report_path, model_id="mock")
    report_text = report_path.read_text(encoding="utf-8")

    assert "Task 29 — MedASR WER Evaluation" in report_text
    assert "MedASR WER Average" in report_text
    assert "MedASR WER per clip" in report_text
