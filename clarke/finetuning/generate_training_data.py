"""Generate synthetic transcript-context-letter triplets for Clarke fine-tuning."""

from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from loguru import logger


LOGGER = logger.bind(component="generate_training_data")
DEFAULT_TOTAL_SAMPLES = 250
DEFAULT_TRAIN_SPLIT = 200
DEFAULT_REVIEW_SAMPLES = 20


@dataclass(frozen=True)
class ScenarioTemplate:
    """Structured template describing one synthetic clinic scenario.

    Args:
        specialty: Clinical specialty bucket.
        diagnosis: Primary diagnosis for the context problem list.
        presenting_issue: Main concern discussed in the transcript.
        medication: Typical medication and dose string.
        lab_name: Representative lab or clinical metric name.
        lab_unit: Unit for the representative metric.
        follow_up: Follow-up recommendation sentence fragment.

    Returns:
        ScenarioTemplate: Immutable scenario descriptor.
    """

    specialty: str
    diagnosis: str
    presenting_issue: str
    medication: str
    lab_name: str
    lab_unit: str
    follow_up: str


SCENARIO_TEMPLATES: list[ScenarioTemplate] = [
    ScenarioTemplate(
        specialty="Diabetes & Endocrinology",
        diagnosis="Type 2 Diabetes Mellitus",
        presenting_issue="rising blood glucose readings and afternoon fatigue",
        medication="Metformin 1g BD",
        lab_name="HbA1c",
        lab_unit="mmol/mol",
        follow_up="repeat blood tests and review in 3 months",
    ),
    ScenarioTemplate(
        specialty="Cardiology",
        diagnosis="Stable Angina",
        presenting_issue="intermittent exertional chest discomfort",
        medication="Atorvastatin 40mg nocte",
        lab_name="Troponin",
        lab_unit="ng/L",
        follow_up="home blood pressure diary and cardiology follow-up in 8 weeks",
    ),
    ScenarioTemplate(
        specialty="Respiratory Medicine",
        diagnosis="Moderate Persistent Asthma",
        presenting_issue="frequent reliever inhaler use and night symptoms",
        medication="Budesonide/Formoterol 200/6mcg BD",
        lab_name="Peak Flow",
        lab_unit="L/min",
        follow_up="inhaler technique check and review in 6 weeks",
    ),
    ScenarioTemplate(
        specialty="Heart Failure Clinic",
        diagnosis="Heart Failure with Reduced Ejection Fraction",
        presenting_issue="breathlessness on exertion and ankle swelling",
        medication="Furosemide 40mg OD",
        lab_name="BNP",
        lab_unit="pg/mL",
        follow_up="daily weight monitoring and heart failure nurse review in 4 weeks",
    ),
    ScenarioTemplate(
        specialty="Mental Health",
        diagnosis="Major Depressive Disorder",
        presenting_issue="low mood, poor sleep, and reduced motivation",
        medication="Sertraline 100mg OD",
        lab_name="PHQ-9",
        lab_unit="score",
        follow_up="continue psychological support and reassess in 4 weeks",
    ),
]


def _iso_date(days_offset: int) -> str:
    """Build an ISO calendar date relative to now.

    Args:
        days_offset: Integer day offset from current UTC date.

    Returns:
        str: Date formatted as YYYY-MM-DD.
    """

    return (datetime.utcnow() + timedelta(days=days_offset)).date().isoformat()


def _build_context(sample_id: int, template: ScenarioTemplate, rng: random.Random) -> dict[str, Any]:
    """Create a PatientContext-like JSON payload for one sample.

    Args:
        sample_id: Numeric identifier for deterministic IDs.
        template: Scenario template to instantiate.
        rng: Random generator used for reproducible values.

    Returns:
        dict[str, Any]: Synthetic PatientContext dictionary.
    """

    patient_id = f"syn-{sample_id:04d}"
    age = rng.randint(28, 82)
    sex = rng.choice(["Female", "Male"])
    lab_value = round(rng.uniform(4.5, 95.0), 1)
    previous_value = max(0.1, round(lab_value + rng.uniform(-8.0, 8.0), 1))
    trend = "rising" if lab_value > previous_value else "falling"

    return {
        "patient_id": patient_id,
        "demographics": {
            "name": f"Patient {sample_id}",
            "dob": _iso_date(-age * 365),
            "nhs_number": f"{rng.randint(100, 999)} {rng.randint(100, 999)} {rng.randint(1000, 9999)}",
            "age": age,
            "sex": sex,
            "address": f"{rng.randint(10, 99)} Example Street, London",
            "specialty": template.specialty,
        },
        "problem_list": [
            f"{template.diagnosis} (active)",
            "Hypertension (active)",
        ],
        "medications": [
            {
                "name": template.medication.split()[0],
                "dose": " ".join(template.medication.split()[1:]),
                "frequency": "As directed",
                "fhir_id": f"med-{sample_id:04d}",
            }
        ],
        "allergies": [
            {
                "substance": "Penicillin",
                "reaction": "Rash",
                "severity": "moderate",
            }
        ],
        "recent_labs": [
            {
                "name": template.lab_name,
                "value": str(lab_value),
                "unit": template.lab_unit,
                "reference_range": "See local lab guidance",
                "date": _iso_date(-rng.randint(5, 45)),
                "trend": trend,
                "previous_value": str(previous_value),
                "previous_date": _iso_date(-rng.randint(46, 120)),
                "fhir_resource_id": f"obs-{sample_id:04d}",
            }
        ],
        "recent_imaging": [],
        "clinical_flags": [f"{template.lab_name} trend is {trend}"],
        "last_letter_excerpt": "Patient remained clinically stable at last review.",
        "retrieval_warnings": [],
        "retrieved_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def _build_transcript(template: ScenarioTemplate, context: dict[str, Any], rng: random.Random) -> str:
    """Compose a consultation transcript with realistic clinic dialogue content.

    Args:
        template: Scenario template with clinical focus terms.
        context: Context dictionary used for factual alignment.
        rng: Random generator used for variant phrases.

    Returns:
        str: Multi-sentence transcript around 170–230 words.
    """

    openings = [
        "Clinician: Thanks for coming in today, let's review how you've been since the last appointment.",
        "Clinician: Good to see you again, I want to check symptoms and your recent results before we plan next steps.",
    ]
    symptom_detail = (
        f"Patient: I have noticed {template.presenting_issue}, and it has been affecting my daily routine over the past few weeks."
    )
    lab_name = context["recent_labs"][0]["name"]
    lab_value = context["recent_labs"][0]["value"]
    medication = template.medication

    segments = [
        rng.choice(openings),
        symptom_detail,
        (
            f"Clinician: Your {lab_name} result is {lab_value} {template.lab_unit}; compared with your previous reading, we need tighter control."
        ),
        (
            f"Clinician: We'll continue {medication}, reinforce adherence, and discuss lifestyle measures including diet, activity, and sleep."
        ),
        "Patient: I understand, and I would appreciate a clear written plan so I can follow it at home.",
        (
            f"Clinician: We agreed on safety-net advice, warning symptoms, and we will {template.follow_up}."
        ),
        "Clinician: I have answered your questions and will send a summary letter to your GP today.",
    ]

    base_text = " ".join(segments)
    filler = (
        " We also reviewed current medications, potential side effects, and agreed that the patient will seek urgent care "
        "if red-flag symptoms worsen before the next clinic review."
    )
    while len(base_text.split()) < 170:
        base_text += filler

    return base_text


def _build_reference_letter(template: ScenarioTemplate, context: dict[str, Any], transcript: str) -> str:
    """Render a concise NHS-style reference clinic letter.

    Args:
        template: Scenario template defining clinical domain.
        context: Context dictionary containing aligned facts.
        transcript: Transcript text for summary grounding.

    Returns:
        str: Reference letter body.
    """

    demographics = context["demographics"]
    lab = context["recent_labs"][0]
    summary_line = " ".join(transcript.split()[:28])
    return (
        f"Dear GP,\n\n"
        f"Re: {demographics['name']} ({demographics['dob']}), NHS {demographics['nhs_number']}\n\n"
        f"Diagnosis: {template.diagnosis}.\n"
        f"Today the patient described {template.presenting_issue}."
        f" Their latest {lab['name']} was {lab['value']} {lab['unit']} ({lab['trend']}).\n"
        f"Medication plan: continue {template.medication} with adherence reinforcement.\n"
        f"Follow-up: {template.follow_up}.\n"
        f"Consultation summary excerpt: {summary_line}...\n\n"
        "Yours sincerely,\n"
        "Dr. Sarah Chen\n"
        "Consultant"
    )


def _call_llm_for_triplet(
    client: httpx.Client,
    model: str,
    api_key: str,
    template: ScenarioTemplate,
) -> dict[str, Any] | None:
    """Attempt one external LLM call for a synthetic triplet.

    Args:
        client: HTTPX client for API communication.
        model: Model name for OpenAI-compatible endpoint.
        api_key: API key credential.
        template: Scenario template guiding prompt content.

    Returns:
        dict[str, Any] | None: Parsed triplet dictionary or None if call failed/invalid.
    """

    prompt = (
        "Generate one JSON object with keys transcript, context, reference_letter for an NHS clinic follow-up. "
        "The transcript should be about 200 words and the context should align factually. "
        f"Specialty: {template.specialty}; diagnosis: {template.diagnosis}; medication: {template.medication}."
    )
    try:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as error:
        LOGGER.warning("LLM generation failed, falling back to template", error=str(error))
    return None


def generate_triplets(total_samples: int, seed: int = 42) -> list[dict[str, Any]]:
    """Generate synthetic triplets using API-assisted or template-only mode.

    Args:
        total_samples: Number of triplets to generate.
        seed: Random seed for reproducibility.

    Returns:
        list[dict[str, Any]]: Generated triplet records.
    """

    rng = random.Random(seed)
    records: list[dict[str, Any]] = []
    api_key = os.getenv("OPENAI_API_KEY", "")
    model_name = os.getenv("TRAINING_DATA_MODEL", "gpt-4o-mini")
    use_api = bool(api_key)

    with httpx.Client() as client:
        for idx in range(1, total_samples + 1):
            template = SCENARIO_TEMPLATES[(idx - 1) % len(SCENARIO_TEMPLATES)]
            candidate = None
            if use_api:
                candidate = _call_llm_for_triplet(client, model_name, api_key, template)
            if candidate is None:
                context = _build_context(idx, template, rng)
                transcript = _build_transcript(template, context, rng)
                letter = _build_reference_letter(template, context, transcript)
                candidate = {
                    "transcript": transcript,
                    "context": context,
                    "reference_letter": letter,
                }
            records.append(candidate)
    return records


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    """Write records to a JSONL file.

    Args:
        records: List of JSON-serializable dictionaries.
        output_path: Destination JSONL file path.

    Returns:
        None: Function writes file in place.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def review_quality(records: list[dict[str, Any]], sample_size: int, seed: int = 99) -> tuple[bool, list[str]]:
    """Run lightweight quality checks over a random subset of records.

    Args:
        records: Generated records to inspect.
        sample_size: Number of records to review.
        seed: Random seed for deterministic review picks.

    Returns:
        tuple[bool, list[str]]: Pass flag and list of failure messages.
    """

    failures: list[str] = []
    rng = random.Random(seed)
    indices = rng.sample(range(len(records)), k=min(sample_size, len(records)))

    for index in indices:
        record = records[index]
        if not {"transcript", "context", "reference_letter"}.issubset(record.keys()):
            failures.append(f"sample {index + 1}: missing required keys")
            continue
        word_count = len(record["transcript"].split())
        if word_count < 150:
            failures.append(f"sample {index + 1}: transcript too short ({word_count} words)")
        context = record["context"]
        if not context.get("problem_list") or not context.get("medications"):
            failures.append(f"sample {index + 1}: incomplete context clinical data")
        if "Dear GP" not in record["reference_letter"]:
            failures.append(f"sample {index + 1}: letter missing NHS salutation")

    return (len(failures) == 0, failures)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for training data generation.

    Args:
        None: Values are read from CLI.

    Returns:
        argparse.Namespace: Parsed options namespace.
    """

    parser = argparse.ArgumentParser(description="Generate synthetic fine-tuning triplets for Clarke")
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL_SAMPLES, help="Total samples to generate")
    parser.add_argument("--train-size", type=int, default=DEFAULT_TRAIN_SPLIT, help="Number of training samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("clarke/data/training"),
        help="Directory for train/test JSONL outputs",
    )
    parser.add_argument(
        "--review-samples",
        type=int,
        default=DEFAULT_REVIEW_SAMPLES,
        help="Number of random samples for quality review",
    )
    return parser.parse_args()


def main() -> int:
    """Generate, split, validate, and save fine-tuning triplet datasets.

    Args:
        None: Uses parsed command-line arguments.

    Returns:
        int: Process exit code (0 success, 1 validation failure).
    """

    args = parse_args()
    if args.train_size >= args.total:
        LOGGER.error("Train size must be smaller than total sample count")
        return 1

    LOGGER.info("Generating synthetic triplets", total=args.total, train_size=args.train_size)
    records = generate_triplets(args.total, seed=args.seed)
    train_records = records[: args.train_size]
    test_records = records[args.train_size :]

    write_jsonl(train_records, args.output_dir / "train.jsonl")
    write_jsonl(test_records, args.output_dir / "test.jsonl")

    quality_pass, failures = review_quality(records, sample_size=args.review_samples)
    if not quality_pass:
        LOGGER.error("Quality review failed", failures=failures)
        return 1

    LOGGER.info(
        "Training data generation complete",
        train_count=len(train_records),
        test_count=len(test_records),
        output_dir=str(args.output_dir),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
