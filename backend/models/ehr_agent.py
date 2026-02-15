"""EHR Agent module for deterministic FHIR retrieval and MedGemma 4B summarisation."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Template
from pydantic import ValidationError

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
except ModuleNotFoundError:  # pragma: no cover - mock mode support
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    BitsAndBytesConfig = None

from backend.config import get_settings
from backend.errors import ModelExecutionError, get_component_logger
from backend.fhir.queries import get_full_patient_context
from backend.schemas import LabResult, PatientContext

logger = get_component_logger("ehr_agent")


DEFAULT_CONTEXT_PROMPT = """You are a clinical EHR synthesis agent.
Given the raw FHIR payload below, output only valid JSON for this schema:
{
  \"patient_id\": \"...\",
  \"demographics\": {...},
  \"problem_list\": [\"...\"],
  \"medications\": [{...}],
  \"allergies\": [{...}],
  \"recent_labs\": [{...}],
  \"recent_imaging\": [{...}],
  \"clinical_flags\": [\"...\"],
  \"last_letter_excerpt\": null,
  \"retrieval_warnings\": [],
  \"retrieved_at\": \"...\"
}

Raw FHIR context JSON:
{{ raw_context_json }}
"""


def parse_agent_output(raw_output: str) -> dict[str, Any]:
    """Extract first JSON object from MedGemma output after stripping prompt leaks.

    Args:
        raw_output (str): Raw model generation text that may contain extra formatting.

    Returns:
        dict[str, Any]: Parsed JSON object extracted from model output.
    """

    cleaned_output = re.sub(r"<\|system\|>.*?<\|end\|>", "", raw_output, flags=re.DOTALL)
    cleaned_output = re.sub(r"```json\s*", "", cleaned_output)
    cleaned_output = re.sub(r"```\s*", "", cleaned_output)
    match = re.search(r"\{[\s\S]*\}", cleaned_output)
    if match:
        return json.loads(match.group())
    raise ValueError("No valid JSON found in agent output")


class EHRAgent:
    """Retrieve raw FHIR context and synthesise a validated PatientContext object.

    Args:
        model_id (str | None): Optional override for MedGemma 4B model ID.

    Returns:
        None: Creates an agent instance with lazy model loading.
    """

    def __init__(self, model_id: str | None = None) -> None:
        settings = get_settings()
        self.model_id = model_id or settings.MEDGEMMA_4B_MODEL_ID
        self.timeout_s = settings.FHIR_TIMEOUT_S
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self.is_mock_mode = self.model_id.lower() == "mock"

    def load_model(self) -> None:
        """Load the MedGemma 4B model/tokenizer in 4-bit mode unless running in mock mode.

        Args:
            None: Uses configured model ID and quantisation settings.

        Returns:
            None: Populates tokenizer/model attributes for inference.
        """

        if self.is_mock_mode:
            logger.info("EHR agent initialised in mock mode")
            return
        if self._model is not None and self._tokenizer is not None:
            return

        if AutoModelForCausalLM is None or AutoTokenizer is None or BitsAndBytesConfig is None or torch is None:
            raise ModelExecutionError("transformers and torch are required for non-mock EHR mode")

        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
            )
            logger.info("Loaded EHR agent model", model_id=self.model_id)
        except Exception as exc:
            raise ModelExecutionError(f"Failed to load MedGemma EHR model: {exc}") from exc

    def get_patient_context(self, patient_id: str) -> PatientContext:
        """Return structured patient context using deterministic FHIR retrieval with robust fallback.

        Args:
            patient_id (str): Patient identifier used across FHIR resources.

        Returns:
            PatientContext: Validated patient context instance for downstream pipeline use.
        """

        raw_context = asyncio.run(get_full_patient_context(patient_id))

        if self.is_mock_mode:
            return self._build_context_from_raw(raw_context)

        self.load_model()
        for attempt in range(1, 3):
            try:
                summarised_context = self._summarise_with_model(raw_context)
                return PatientContext.model_validate(summarised_context)
            except (ValidationError, ValueError, ModelExecutionError, json.JSONDecodeError) as exc:
                logger.warning(
                    "EHR model summarisation failed; retrying or falling back",
                    patient_id=patient_id,
                    attempt=attempt,
                    error=str(exc),
                )

        fallback_context = self._build_context_from_raw(raw_context)
        fallback_context.retrieval_warnings.append(
            "MedGemma summarisation unavailable; context built via deterministic extraction."
        )
        return fallback_context

    def _summarise_with_model(self, raw_context: dict[str, Any]) -> dict[str, Any]:
        """Run MedGemma generation and parse into a dictionary payload.

        Args:
            raw_context (dict[str, Any]): Deterministic FHIR aggregation from tool queries.

        Returns:
            dict[str, Any]: Parsed context dictionary extracted from model output JSON.
        """

        if self._model is None or self._tokenizer is None:
            raise ModelExecutionError("Model and tokenizer must be loaded before inference")

        prompt = self._render_context_prompt(raw_context)
        inputs = self._tokenizer(prompt, return_tensors="pt")
        if hasattr(self._model, "device"):
            inputs = {key: value.to(self._model.device) for key, value in inputs.items()}

        try:
            output_tokens = self._model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.2,
                top_p=0.9,
                repetition_penalty=1.1,
            )
        except Exception as exc:
            raise ModelExecutionError(f"MedGemma EHR generation failed: {exc}") from exc

        raw_output = self._tokenizer.decode(output_tokens[0], skip_special_tokens=True)
        return parse_agent_output(raw_output)

    def _render_context_prompt(self, raw_context: dict[str, Any]) -> str:
        """Render context synthesis prompt from Jinja template or built-in fallback template.

        Args:
            raw_context (dict[str, Any]): Deterministic FHIR context dictionary.

        Returns:
            str: Prompt text for MedGemma summarisation.
        """

        prompt_template_path = Path("backend/prompts/context_synthesis.j2")
        if prompt_template_path.exists():
            template_text = prompt_template_path.read_text(encoding="utf-8")
        else:
            template_text = DEFAULT_CONTEXT_PROMPT

        template = Template(template_text)
        return template.render(raw_context_json=json.dumps(raw_context, ensure_ascii=False, indent=2))

    def _build_context_from_raw(self, raw_context: dict[str, Any]) -> PatientContext:
        """Construct PatientContext directly from raw FHIR resources as deterministic fallback.

        Args:
            raw_context (dict[str, Any]): Deterministic FHIR context dictionary.

        Returns:
            PatientContext: Fully structured context generated without model summarisation.
        """

        patient = raw_context.get("patients", [{}])[0] if raw_context.get("patients") else {}
        demographics = self._extract_demographics(patient)
        problem_list = self._extract_problem_list(raw_context.get("conditions", []))
        medications = self._extract_medications(raw_context.get("medications", []))
        allergies = self._extract_allergies(raw_context.get("allergies", []))
        recent_labs = self._extract_labs(raw_context.get("observations", []))
        recent_imaging = self._extract_imaging(raw_context.get("diagnostic_reports", []))

        clinical_flags: list[str] = []
        hba1c_values = [lab for lab in recent_labs if lab.name.lower() == "hba1c"]
        if len(hba1c_values) >= 2:
            latest = float(hba1c_values[0].value)
            previous = float(hba1c_values[1].value)
            if latest > previous:
                clinical_flags.append(f"HbA1c rising trend ({hba1c_values[1].value} → {hba1c_values[0].value})")

        return PatientContext(
            patient_id=str(raw_context.get("patient_id", "")),
            demographics=demographics,
            problem_list=problem_list,
            medications=medications,
            allergies=allergies,
            recent_labs=recent_labs,
            recent_imaging=recent_imaging,
            clinical_flags=clinical_flags,
            last_letter_excerpt=None,
            retrieval_warnings=[],
            retrieved_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    @staticmethod
    def _extract_demographics(patient: dict[str, Any]) -> dict[str, Any]:
        """Extract demographics map from FHIR Patient resource.

        Args:
            patient (dict[str, Any]): FHIR Patient resource dictionary.

        Returns:
            dict[str, Any]: Simplified demographics payload.
        """

        names = patient.get("name", [])
        first_name = names[0] if names else {}
        full_name_parts = first_name.get("prefix", []) + first_name.get("given", []) + [first_name.get("family", "")]
        full_name = " ".join(part for part in full_name_parts if part).strip()

        nhs_number = ""
        for identifier in patient.get("identifier", []):
            if "nhs" in str(identifier.get("system", "")).lower() or identifier.get("value"):
                nhs_number = str(identifier.get("value", ""))
                if nhs_number:
                    break

        birth_date_raw = str(patient.get("birthDate", ""))
        dob_display = birth_date_raw
        age: int | None = None
        if birth_date_raw:
            try:
                parsed_dob = date.fromisoformat(birth_date_raw)
                dob_display = parsed_dob.strftime("%d/%m/%Y")
                today = date.today()
                age = today.year - parsed_dob.year - ((today.month, today.day) < (parsed_dob.month, parsed_dob.day))
            except ValueError:
                dob_display = birth_date_raw

        nhs_clean = "".join(ch for ch in nhs_number if ch.isdigit())
        if len(nhs_clean) == 10:
            nhs_number = f"{nhs_clean[:3]}-{nhs_clean[3:6]}-{nhs_clean[6:]}"

        return {
            "name": full_name,
            "dob": dob_display,
            "nhs_number": nhs_number,
            "age": age,
            "sex": str(patient.get("gender", "")).capitalize(),
            "address": "",
        }

    @staticmethod
    def _extract_problem_list(conditions: list[dict[str, Any]]) -> list[str]:
        """Extract active problem list from FHIR Condition resources.

        Args:
            conditions (list[dict[str, Any]]): List of FHIR Condition resources.

        Returns:
            list[str]: Human-readable problem entries.
        """

        problems: list[str] = []
        for condition in conditions:
            status_codes = condition.get("clinicalStatus", {}).get("coding", [])
            is_active = any(code.get("code") == "active" for code in status_codes) if status_codes else True
            label = str(condition.get("code", {}).get("text", "")).strip()
            if is_active and label:
                problems.append(label)
        return problems

    @staticmethod
    def _extract_medications(medications: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract simplified medication entries from MedicationRequest resources.

        Args:
            medications (list[dict[str, Any]]): List of FHIR MedicationRequest resources.

        Returns:
            list[dict[str, Any]]: Medication records with source IDs.
        """

        extracted: list[dict[str, Any]] = []
        for medication in medications:
            dosage_text = ""
            dosage_instructions = medication.get("dosageInstruction", [])
            if dosage_instructions:
                dosage_text = str(dosage_instructions[0].get("text", "")).strip()

            dose = ""
            frequency = ""
            if dosage_text:
                parts = dosage_text.rsplit(" ", maxsplit=1)
                if len(parts) == 2:
                    dose, frequency = parts[0], parts[1]
                else:
                    dose = dosage_text

            extracted.append(
                {
                    "name": str(medication.get("medicationCodeableConcept", {}).get("text", "")).strip(),
                    "dose": dose,
                    "frequency": frequency,
                    "fhir_id": str(medication.get("id", "")),
                }
            )
        return extracted

    @staticmethod
    def _extract_allergies(allergies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract allergy summary records from AllergyIntolerance resources.

        Args:
            allergies (list[dict[str, Any]]): List of FHIR AllergyIntolerance resources.

        Returns:
            list[dict[str, Any]]: Simplified allergy entries.
        """

        extracted: list[dict[str, Any]] = []
        for allergy in allergies:
            reaction = ""
            reactions = allergy.get("reaction", [])
            if reactions:
                manifestations = reactions[0].get("manifestation", [])
                if manifestations:
                    reaction = str(manifestations[0].get("text", ""))
            extracted.append(
                {
                    "substance": str(allergy.get("code", {}).get("text", "")).strip(),
                    "reaction": reaction,
                    "severity": str(allergy.get("criticality", "")).strip() or "unknown",
                }
            )
        return extracted

    @staticmethod
    def _extract_labs(observations: list[dict[str, Any]]) -> list[LabResult]:
        """Extract laboratory results from Observation resources with simple trend linkage.

        Args:
            observations (list[dict[str, Any]]): List of FHIR Observation resources.

        Returns:
            list[LabResult]: Structured laboratory results sorted by effective date.
        """

        labs: list[LabResult] = []
        sorted_observations = sorted(
            observations,
            key=lambda obs: str(obs.get("effectiveDateTime", "")),
            reverse=True,
        )
        previous_by_name: dict[str, LabResult] = {}

        for observation in sorted_observations:
            quantity = observation.get("valueQuantity", {})
            name = str(observation.get("code", {}).get("text", "")).strip()
            value = str(quantity.get("value", ""))
            unit = str(quantity.get("unit", ""))
            date = str(observation.get("effectiveDateTime", ""))
            lab = LabResult(
                name=name,
                value=value,
                unit=unit,
                date=date,
                fhir_resource_id=str(observation.get("id", "")),
            )
            if name in previous_by_name:
                previous = previous_by_name[name]
                lab.previous_value = previous.value
                lab.previous_date = previous.date
                try:
                    current_val = float(lab.value)
                    previous_val = float(previous.value)
                    if current_val > previous_val:
                        lab.trend = "rising"
                    elif current_val < previous_val:
                        lab.trend = "falling"
                    else:
                        lab.trend = "stable"
                except (TypeError, ValueError):
                    lab.trend = None
            previous_by_name[name] = lab
            labs.append(lab)

        return labs

    @staticmethod
    def _extract_imaging(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract concise imaging/report summaries from DiagnosticReport resources.

        Args:
            reports (list[dict[str, Any]]): List of FHIR DiagnosticReport resources.

        Returns:
            list[dict[str, Any]]: Recent report summary entries.
        """

        extracted: list[dict[str, Any]] = []
        for report in reports:
            extracted.append(
                {
                    "type": str(report.get("code", {}).get("text", "Diagnostic report")),
                    "date": str(report.get("effectiveDateTime", "")),
                    "summary": str(report.get("conclusion", "")).strip(),
                }
            )
        return extracted
