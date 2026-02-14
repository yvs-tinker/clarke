"""Evaluate document generation quality using BLEU, ROUGE-L, and manual-review heuristics."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rouge_score import rouge_scorer
from sacrebleu import corpus_bleu

from backend.errors import get_component_logger
from backend.models.doc_generator import KNOWN_SECTION_HEADINGS, DocumentGenerator
from backend.schemas import PatientContext

logger = get_component_logger("eval_doc_gen")


@dataclass(frozen=True)
class GeneratedLetterRecord:
    """Container for one generated letter and its reference text.

    Args:
        index (int): Zero-based sample index.
        transcript (str): Source consultation transcript.
        generated_letter (str): Model-generated clinic letter text.
        reference_letter (str): Gold reference letter text.

    Returns:
        None: Dataclass value object.
    """

    index: int
    transcript: str
    generated_letter: str
    reference_letter: str


@dataclass(frozen=True)
class ManualReviewResult:
    """Container for manual-review proxy checks over sampled letters.

    Args:
        sample_size (int): Number of letters manually sampled.
        nhs_format_pass_rate (float): Share of sampled letters passing heading checks.
        clinical_accuracy_pass_rate (float): Share of sampled letters passing similarity threshold.

    Returns:
        None: Dataclass value object.
    """

    sample_size: int
    nhs_format_pass_rate: float
    clinical_accuracy_pass_rate: float


def load_test_triplets(test_path: Path, sample_limit: int) -> list[dict[str, object]]:
    """Load document-generation evaluation records from JSONL.

    Args:
        test_path (Path): Path to `data/training/test.jsonl`.
        sample_limit (int): Maximum number of records to evaluate.

    Returns:
        list[dict[str, object]]: Parsed list of transcript/context/reference triplets.
    """

    raw_lines = test_path.read_text(encoding="utf-8").splitlines()
    parsed_records = [json.loads(line) for line in raw_lines if line.strip()]
    return parsed_records[:sample_limit]


def generate_letters(records: list[dict[str, object]], model_id: str) -> list[GeneratedLetterRecord]:
    """Generate clinic letters for each triplet using the configured generator model.

    Args:
        records (list[dict[str, object]]): Loaded test triplets.
        model_id (str): Model identifier passed to `DocumentGenerator`.

    Returns:
        list[GeneratedLetterRecord]: Generated and reference letter pairs.
    """

    generator = DocumentGenerator(model_id=model_id)
    generated_records: list[GeneratedLetterRecord] = []

    for index, record in enumerate(records):
        context = PatientContext.model_validate(record["context"])
        transcript = str(record["transcript"])
        reference_letter = str(record["reference_letter"])
        document = generator.generate_document(transcript=transcript, context=context)
        generated_records.append(
            GeneratedLetterRecord(
                index=index,
                transcript=transcript,
                generated_letter=render_document_text(document.sections),
                reference_letter=reference_letter,
            )
        )

    return generated_records


def render_document_text(sections: list) -> str:
    """Render ClinicalDocument sections into plain-text letter content for metrics.

    Args:
        sections (list): Document sections with heading/content attributes.

    Returns:
        str: Newline-delimited heading/content text.
    """

    return "\n".join(f"{section.heading}\n{section.content}" for section in sections)


def compute_bleu_rouge(records: list[GeneratedLetterRecord]) -> tuple[float, float]:
    """Compute corpus BLEU and mean ROUGE-L F1 for generated letters.

    Args:
        records (list[GeneratedLetterRecord]): Generated/reference letter pairs.

    Returns:
        tuple[float, float]: BLEU score (0-100) and average ROUGE-L F1 (0-1).
    """

    hypotheses = [record.generated_letter for record in records]
    references = [record.reference_letter for record in records]

    bleu_score = float(corpus_bleu(hypotheses, [references]).score)

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    rouge_scores = [
        scorer.score(target=record.reference_letter, prediction=record.generated_letter)["rougeL"].fmeasure
        for record in records
    ]
    rouge_l_average = sum(rouge_scores) / len(rouge_scores)

    return bleu_score, rouge_l_average


def run_manual_review(records: list[GeneratedLetterRecord], review_sample_size: int) -> ManualReviewResult:
    """Run deterministic proxy checks for manual formatting and clinical-content review.

    Args:
        records (list[GeneratedLetterRecord]): Generated/reference letter pairs.
        review_sample_size (int): Number of leading records to inspect.

    Returns:
        ManualReviewResult: Manual-review proxy pass rates.
    """

    sample = records[:review_sample_size]
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

    format_passes = 0
    clinical_passes = 0
    for record in sample:
        generated_lower = record.generated_letter.lower()
        has_all_headings = all(heading.lower() in generated_lower for heading in KNOWN_SECTION_HEADINGS)
        format_passes += int(has_all_headings)

        rouge_l = scorer.score(target=record.reference_letter, prediction=record.generated_letter)["rougeL"].fmeasure
        clinical_passes += int(rouge_l >= 0.30)

    return ManualReviewResult(
        sample_size=len(sample),
        nhs_format_pass_rate=format_passes / len(sample),
        clinical_accuracy_pass_rate=clinical_passes / len(sample),
    )


def fine_tuned_adapter_available(adapter_dir: Path) -> bool:
    """Check whether a LoRA adapter checkpoint exists for fine-tuned comparisons.

    Args:
        adapter_dir (Path): Directory where Task 28 saves adapter artifacts.

    Returns:
        bool: True when at least one adapter artifact besides README exists.
    """

    if not adapter_dir.exists():
        return False
    return any(path.name.lower() != "readme.md" for path in adapter_dir.iterdir())


def append_results_to_report(
    *,
    report_path: Path,
    test_sample_size: int,
    model_id: str,
    bleu_score: float,
    rouge_l: float,
    manual_review: ManualReviewResult,
    fine_tuned_available: bool,
) -> None:
    """Append Task 31 evaluation metrics and notes to `evaluation_report.md`.

    Args:
        report_path (Path): Markdown file receiving appended evaluation output.
        test_sample_size (int): Number of evaluated test triplets.
        model_id (str): Generator model used for this run.
        bleu_score (float): Corpus BLEU score.
        rouge_l (float): Average ROUGE-L F1 score.
        manual_review (ManualReviewResult): Proxy manual-review results.
        fine_tuned_available (bool): Whether adapter artifacts were found.

    Returns:
        None: Writes lines to report file.
    """

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    fine_tuned_note = (
        "fine-tuned adapter detected (comparison path available)"
        if fine_tuned_available
        else "fine-tuned adapter not found (baseline-only evaluation)"
    )
    lines = [
        "\n## Task 31 — Document Generation Evaluation",
        f"- Timestamp (UTC): {timestamp}",
        f"- Evaluated Samples: {test_sample_size}",
        f"- Model: {model_id}",
        f"- BLEU: {bleu_score:.4f}",
        f"- ROUGE-L: {rouge_l:.4f}",
        f"- Manual Review (n={manual_review.sample_size}): NHS format pass rate={manual_review.nhs_format_pass_rate:.2%}, clinical accuracy pass rate={manual_review.clinical_accuracy_pass_rate:.2%}",
        f"- Fine-tuned comparison status: {fine_tuned_note}",
    ]

    with report_path.open("a", encoding="utf-8") as report_handle:
        report_handle.write("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    """Parse CLI options for Task 31 document-generation evaluation.

    Args:
        None: Reads command-line arguments.

    Returns:
        argparse.Namespace: Parsed argument set.
    """

    parser = argparse.ArgumentParser(description="Task 31: Document generation BLEU/ROUGE-L evaluation")
    parser.add_argument("--test-path", type=Path, default=Path("data/training/test.jsonl"))
    parser.add_argument("--report-path", type=Path, default=Path("evaluation_report.md"))
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--review-sample-size", type=int, default=10)
    parser.add_argument("--model-id", type=str, default="mock")
    parser.add_argument("--adapter-dir", type=Path, default=Path("finetuning/adapter"))
    return parser.parse_args()


def main() -> None:
    """Run Task 31 metrics pipeline and print concise terminal summary.

    Args:
        None: Script entrypoint.

    Returns:
        None: Persists metrics and logs summary.
    """

    args = parse_args()
    records = load_test_triplets(test_path=args.test_path, sample_limit=args.sample_size)
    generated_records = generate_letters(records=records, model_id=args.model_id)
    bleu_score, rouge_l = compute_bleu_rouge(generated_records)
    manual_review = run_manual_review(generated_records, review_sample_size=args.review_sample_size)
    has_adapter = fine_tuned_adapter_available(args.adapter_dir)

    append_results_to_report(
        report_path=args.report_path,
        test_sample_size=len(generated_records),
        model_id=args.model_id,
        bleu_score=bleu_score,
        rouge_l=rouge_l,
        manual_review=manual_review,
        fine_tuned_available=has_adapter,
    )

    logger.info(
        "Document generation evaluation complete",
        sample_size=len(generated_records),
        bleu=bleu_score,
        rouge_l=rouge_l,
        nhs_format_pass_rate=manual_review.nhs_format_pass_rate,
        clinical_accuracy_pass_rate=manual_review.clinical_accuracy_pass_rate,
    )
    print(f"BLEU: {bleu_score:.4f}")
    print(f"ROUGE-L: {rouge_l:.4f}")


if __name__ == "__main__":
    main()
