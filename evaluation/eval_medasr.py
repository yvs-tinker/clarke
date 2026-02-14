"""Evaluate MedASR Word Error Rate on Clarke demo audio clips."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from jiwer import wer

from backend.models.medasr import MedASRModel


@dataclass(frozen=True)
class WerResult:
    """Container for per-clip WER outputs.

    Args:
        clip_name (str): Audio clip stem name.
        reference_words (int): Number of words in ground-truth transcript.
        hypothesis_words (int): Number of words in model transcript.
        wer_score (float): Word error rate in range [0, +inf).

    Returns:
        None: Dataclass value object.
    """

    clip_name: str
    reference_words: int
    hypothesis_words: int
    wer_score: float


DEMO_CLIPS: tuple[tuple[str, str], ...] = (
    ("mrs_thompson", "data/demo/mrs_thompson.wav"),
    ("mr_okafor", "data/demo/mr_okafor.wav"),
    ("ms_patel", "data/demo/ms_patel.wav"),
)


def read_transcript(path: Path) -> str:
    """Read and normalize a transcript file.

    Args:
        path (Path): Path to transcript text file.

    Returns:
        str: Transcript content stripped of leading/trailing whitespace.
    """

    return path.read_text(encoding="utf-8").strip()


def calculate_wer(reference_text: str, hypothesis_text: str) -> float:
    """Compute WER for a reference and hypothesis text pair.

    Args:
        reference_text (str): Ground-truth transcript string.
        hypothesis_text (str): Predicted transcript string.

    Returns:
        float: Word error rate score computed by jiwer.wer.
    """

    return float(wer(reference_text, hypothesis_text))


def run_medasr_evaluation(force_mock: bool = True) -> tuple[list[WerResult], str]:
    """Run WER evaluation for all three demo clips using MedASR.

    Args:
        force_mock (bool): Whether to force MEDASR_MODEL_ID=mock for deterministic evaluation.

    Returns:
        tuple[list[WerResult], str]: Results list and effective model id used.
    """

    if force_mock:
        os.environ["MEDASR_MODEL_ID"] = "mock"

    model = MedASRModel()
    results: list[WerResult] = []

    for clip_name, audio_path in DEMO_CLIPS:
        reference_path = Path(f"data/demo/{clip_name}_transcript.txt")
        reference_text = read_transcript(reference_path)
        transcript = model.transcribe(audio_path)
        score = calculate_wer(reference_text, transcript.text)
        results.append(
            WerResult(
                clip_name=clip_name,
                reference_words=len(reference_text.split()),
                hypothesis_words=transcript.word_count,
                wer_score=score,
            )
        )

    return results, model.settings.MEDASR_MODEL_ID


def append_results_to_report(results: list[WerResult], report_path: Path, model_id: str) -> None:
    """Append formatted MedASR WER evaluation output to markdown report.

    Args:
        results (list[WerResult]): Per-clip WER results.
        report_path (Path): Markdown report path for appending results.
        model_id (str): MedASR model identifier used for evaluation.

    Returns:
        None: Writes section to report file.
    """

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    average_wer = sum(item.wer_score for item in results) / len(results)

    lines = [
        "\n## Task 29 — MedASR WER Evaluation",
        f"- Timestamp (UTC): {timestamp}",
        f"- Model: {model_id}",
        f"- MedASR WER Average: {average_wer:.4f}",
        "- MedASR WER per clip:",
    ]

    for item in results:
        lines.append(
            (
                f"  - {item.clip_name}: WER={item.wer_score:.4f} "
                f"(reference_words={item.reference_words}, hypothesis_words={item.hypothesis_words})"
            )
        )

    if average_wer > 0.15:
        lines.append(
            "- Note: MedASR WER exceeded 15% on demo clips; consider dictation-style audio fallback "
            "(implementation fallback path #4)."
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line options for MedASR evaluation.

    Args:
        None: Reads process argv.

    Returns:
        argparse.Namespace: Parsed CLI flags.
    """

    parser = argparse.ArgumentParser(description="Evaluate MedASR WER on demo clips.")
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("evaluation_report.md"),
        help="Path to markdown report file.",
    )
    parser.add_argument(
        "--no-force-mock",
        action="store_true",
        help="Do not force MEDASR_MODEL_ID=mock.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute CLI evaluation flow and append markdown results.

    Args:
        None: CLI entrypoint.

    Returns:
        None: Writes report and prints summary.
    """

    args = parse_args()
    results, model_id = run_medasr_evaluation(force_mock=not args.no_force_mock)
    append_results_to_report(results=results, report_path=args.report_path, model_id=model_id)

    average_wer = sum(item.wer_score for item in results) / len(results)
    print(f"MedASR WER Average: {average_wer:.4f}")
    for item in results:
        print(f"{item.clip_name}: {item.wer_score:.4f}")


if __name__ == "__main__":
    main()
