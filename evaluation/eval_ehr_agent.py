"""Evaluate EHR agent fact recall, precision, and hallucination on demo patients."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.models.ehr_agent import EHRAgent
from backend.schemas import PatientContext


@dataclass(frozen=True)
class PatientMetricResult:
    """Container for per-patient EHR fact evaluation metrics.

    Args:
        patient_id (str): Patient identifier.
        recall (float): Gold fact recall ratio in range [0, 1].
        precision (float): Output fact precision ratio in range [0, 1].
        hallucination_rate (float): Output hallucination ratio in range [0, 1].
        matched_count (int): Number of matched facts.
        gold_count (int): Number of gold facts.
        output_count (int): Number of extracted output facts.

    Returns:
        None: Dataclass value object.
    """

    patient_id: str
    recall: float
    precision: float
    hallucination_rate: float
    matched_count: int
    gold_count: int
    output_count: int


@dataclass(frozen=True)
class AggregateMetricResult:
    """Container for average metrics across all demo patients.

    Args:
        recall (float): Mean recall over patients.
        precision (float): Mean precision over patients.
        hallucination_rate (float): Mean hallucination rate over patients.

    Returns:
        None: Dataclass value object.
    """

    recall: float
    precision: float
    hallucination_rate: float


DEMO_PATIENT_IDS: tuple[str, ...] = ("pt-001", "pt-002", "pt-003", "pt-004", "pt-005")


def normalise_fact(fact_text: str) -> str:
    """Normalise a fact string for robust set-based comparison.

    Args:
        fact_text (str): Raw fact text to normalise.

    Returns:
        str: Lowercased alphanumeric/space/punctuation-normalised fact text.
    """

    return " ".join(str(fact_text).strip().lower().split())


def load_gold_facts(patient_id: str, gold_dir: Path) -> set[str]:
    """Load a patient's gold-standard facts from JSON.

    Args:
        patient_id (str): Target patient identifier.
        gold_dir (Path): Directory containing per-patient gold JSON files.

    Returns:
        set[str]: Normalised fact set for the patient.
    """

    file_path = gold_dir / f"{patient_id}.json"
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    return {normalise_fact(fact) for fact in payload["gold_facts"]}


def extract_context_facts(patient_context: PatientContext) -> set[str]:
    """Extract comparable fact strings from a `PatientContext` object.

    Args:
        patient_context (PatientContext): Structured context produced by EHR Agent logic.

    Returns:
        set[str]: Normalised output fact set.
    """

    output_facts: set[str] = set()
    demographics = patient_context.demographics

    if demographics.get("name"):
        output_facts.add(normalise_fact(f"name: {demographics['name']}"))
    if demographics.get("dob"):
        output_facts.add(normalise_fact(f"dob: {demographics['dob']}"))
    if demographics.get("sex"):
        output_facts.add(normalise_fact(f"sex: {demographics['sex']}"))

    for problem in patient_context.problem_list:
        output_facts.add(normalise_fact(f"problem: {problem}"))

    for medication in patient_context.medications:
        medication_name = medication.get("name", "")
        if medication_name:
            output_facts.add(normalise_fact(f"medication: {medication_name}"))

    for allergy in patient_context.allergies:
        substance = allergy.get("substance", "")
        if substance:
            output_facts.add(normalise_fact(f"allergy: {substance}"))
        severity = allergy.get("severity", "")
        if substance and severity:
            output_facts.add(normalise_fact(f"allergy severity: {substance}={severity}"))

    for lab in patient_context.recent_labs:
        if lab.name and lab.value:
            output_facts.add(normalise_fact(f"lab: {lab.name}={lab.value} {lab.unit}"))

    for report in patient_context.recent_imaging:
        report_type = report.get("type", "")
        report_summary = report.get("summary", "")
        if report_type:
            output_facts.add(normalise_fact(f"report type: {report_type}"))
        if report_summary:
            output_facts.add(normalise_fact(f"report summary: {report_summary}"))

    for flag in patient_context.clinical_flags:
        output_facts.add(normalise_fact(f"clinical flag: {flag}"))

    return output_facts


def build_raw_context_from_bundle(patient_id: str, bundle_path: Path) -> dict[str, Any]:
    """Transform a patient bundle into `get_full_patient_context`-shaped raw context.

    Args:
        patient_id (str): Patient identifier.
        bundle_path (Path): Path to a FHIR bundle JSON file.

    Returns:
        dict[str, Any]: Raw context dictionary with resource lists grouped by type.
    """

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    resources_by_type: dict[str, list[dict[str, Any]]] = {
        "Patient": [],
        "Condition": [],
        "MedicationRequest": [],
        "Observation": [],
        "AllergyIntolerance": [],
        "DiagnosticReport": [],
        "Encounter": [],
    }

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        if resource_type in resources_by_type:
            resources_by_type[resource_type].append(resource)

    return {
        "patient_id": patient_id,
        "patients": resources_by_type["Patient"],
        "conditions": resources_by_type["Condition"],
        "medications": resources_by_type["MedicationRequest"],
        "observations": resources_by_type["Observation"],
        "allergies": resources_by_type["AllergyIntolerance"],
        "diagnostic_reports": resources_by_type["DiagnosticReport"],
        "encounters": resources_by_type["Encounter"],
    }


def evaluate_patient(patient_id: str, gold_dir: Path, bundle_dir: Path, agent: EHRAgent) -> PatientMetricResult:
    """Evaluate EHR context facts for one patient against gold standards.

    Args:
        patient_id (str): Patient identifier.
        gold_dir (Path): Directory of gold standard files.
        bundle_dir (Path): Directory of FHIR bundle files.
        agent (EHRAgent): EHR agent instance used for context synthesis.

    Returns:
        PatientMetricResult: Calculated metrics and raw counts.
    """

    gold_facts = load_gold_facts(patient_id=patient_id, gold_dir=gold_dir)
    raw_context = build_raw_context_from_bundle(patient_id=patient_id, bundle_path=bundle_dir / f"{patient_id}.json")
    predicted_context = agent._build_context_from_raw(raw_context)
    output_facts = extract_context_facts(predicted_context)

    matched_facts = gold_facts & output_facts

    recall = len(matched_facts) / len(gold_facts) if gold_facts else 0.0
    precision = len(matched_facts) / len(output_facts) if output_facts else 0.0
    hallucination_rate = (len(output_facts - gold_facts) / len(output_facts)) if output_facts else 0.0

    return PatientMetricResult(
        patient_id=patient_id,
        recall=recall,
        precision=precision,
        hallucination_rate=hallucination_rate,
        matched_count=len(matched_facts),
        gold_count=len(gold_facts),
        output_count=len(output_facts),
    )


def evaluate_all_patients(gold_dir: Path, bundle_dir: Path) -> tuple[list[PatientMetricResult], AggregateMetricResult]:
    """Run EHR fact evaluation for all five demo patients.

    Args:
        gold_dir (Path): Directory of per-patient gold standard files.
        bundle_dir (Path): Directory of FHIR bundle files.

    Returns:
        tuple[list[PatientMetricResult], AggregateMetricResult]: Per-patient and aggregate metrics.
    """

    agent = EHRAgent(model_id="mock")
    patient_results = [
        evaluate_patient(patient_id=patient_id, gold_dir=gold_dir, bundle_dir=bundle_dir, agent=agent)
        for patient_id in DEMO_PATIENT_IDS
    ]

    aggregate = AggregateMetricResult(
        recall=sum(item.recall for item in patient_results) / len(patient_results),
        precision=sum(item.precision for item in patient_results) / len(patient_results),
        hallucination_rate=sum(item.hallucination_rate for item in patient_results) / len(patient_results),
    )
    return patient_results, aggregate


def append_results_to_report(
    patient_results: list[PatientMetricResult],
    aggregate_result: AggregateMetricResult,
    report_path: Path,
) -> None:
    """Append Task 30 evaluation results to markdown report.

    Args:
        patient_results (list[PatientMetricResult]): Metrics for each demo patient.
        aggregate_result (AggregateMetricResult): Average metrics across patients.
        report_path (Path): Report file to append to.

    Returns:
        None: Appends a markdown section to the report.
    """

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    recall_target_hit = aggregate_result.recall > 0.85
    precision_target_hit = aggregate_result.precision > 0.90
    hallucination_target_hit = aggregate_result.hallucination_rate < 0.10

    lines = [
        "\n## Task 30 — EHR Agent Fact Recall Evaluation",
        f"- Timestamp (UTC): {timestamp}",
        "- Targets: recall > 85%, precision > 90%, hallucination < 10%",
        f"- Fact Recall Average: {aggregate_result.recall:.4f}",
        f"- Precision Average: {aggregate_result.precision:.4f}",
        f"- Hallucination Rate Average: {aggregate_result.hallucination_rate:.4f}",
        (
            "- Target Status: "
            f"recall={'PASS' if recall_target_hit else 'FAIL'}, "
            f"precision={'PASS' if precision_target_hit else 'FAIL'}, "
            f"hallucination={'PASS' if hallucination_target_hit else 'FAIL'}"
        ),
        "- Per-patient metrics:",
    ]

    for result in patient_results:
        lines.append(
            (
                f"  - {result.patient_id}: recall={result.recall:.4f}, "
                f"precision={result.precision:.4f}, hallucination={result.hallucination_rate:.4f} "
                f"(matched={result.matched_count}, gold={result.gold_count}, output={result.output_count})"
            )
        )

    if not (recall_target_hit and precision_target_hit and hallucination_target_hit):
        lines.append(
            "- Note: One or more targets were missed; review EHR prompt quality and deterministic extraction mapping."
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line options for EHR fact evaluation.

    Args:
        None: Reads process argv.

    Returns:
        argparse.Namespace: Parsed command line options.
    """

    parser = argparse.ArgumentParser(description="Evaluate EHR agent fact recall/precision/hallucination.")
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=Path("evaluation/gold_standards"),
        help="Directory containing per-patient gold standard JSON files.",
    )
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=Path("data/fhir_bundles"),
        help="Directory containing patient FHIR bundle JSON files.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("evaluation_report.md"),
        help="Markdown report path for appending results.",
    )
    return parser.parse_args()


def main() -> None:
    """Run Task 30 evaluation workflow and append results to report.

    Args:
        None: CLI entrypoint.

    Returns:
        None: Prints summary and writes markdown report section.
    """

    args = parse_args()
    patient_results, aggregate_result = evaluate_all_patients(gold_dir=args.gold_dir, bundle_dir=args.bundle_dir)
    append_results_to_report(
        patient_results=patient_results,
        aggregate_result=aggregate_result,
        report_path=args.report_path,
    )

    print(f"Fact Recall Average: {aggregate_result.recall:.4f}")
    print(f"Precision Average: {aggregate_result.precision:.4f}")
    print(f"Hallucination Rate Average: {aggregate_result.hallucination_rate:.4f}")
    for result in patient_results:
        print(
            f"{result.patient_id}: recall={result.recall:.4f}, "
            f"precision={result.precision:.4f}, hallucination={result.hallucination_rate:.4f}"
        )


if __name__ == "__main__":
    main()
