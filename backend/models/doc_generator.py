"""MedGemma 27B document generation wrapper with prompt rendering and section parsing."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from jinja2 import Environment, FileSystemLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from backend.config import get_settings
from backend.errors import ModelExecutionError, get_component_logger
from backend.schemas import ClinicalDocument, ConsultationStatus, DocumentSection, PatientContext

logger = get_component_logger("doc_generator")

PROMPTS_DIR = Path("backend/prompts")
KNOWN_SECTION_HEADINGS = [
    "History of presenting complaint",
    "Examination findings",
    "Investigation results",
    "Assessment and plan",
    "Current medications",
]


class DocumentGenerator:
    """Generate NHS clinic letters from transcript + patient context using MedGemma 27B.

    Args:
        model_id (str | None): Optional model identifier override.

    Returns:
        None: Initialises lazy model/tokenizer handles and runtime settings.
    """

    def __init__(self, model_id: str | None = None) -> None:
        """Initialise document generator model wrapper state.

        Args:
            model_id (str | None): Optional model identifier override.

        Returns:
            None: Stores settings and lazy-loaded model state.
        """

        self.settings = get_settings()
        self.model_id = model_id or self.settings.MEDGEMMA_27B_MODEL_ID
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self.is_mock_mode = self.model_id.lower() == "mock"

    def load_model(self) -> None:
        """Load MedGemma 27B tokenizer and model in 4-bit quantised mode.

        Args:
            None: Reads class configuration and settings values.

        Returns:
            None: Populates model/tokenizer attributes or mock sentinel state.
        """

        if self.is_mock_mode:
            logger.info("Document generator initialised in mock mode")
            self._tokenizer = "mock"
            self._model = "mock"
            return
        if self._model is not None and self._tokenizer is not None:
            return

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
            logger.info("Loaded MedGemma document model", model_id=self.model_id)
        except Exception as exc:
            raise ModelExecutionError(f"Failed to load MedGemma 27B model: {exc}") from exc

    def generate(self, prompt: str, max_new_tokens: int | None = None) -> str:
        """Generate raw letter text from a rendered prompt.

        Args:
            prompt (str): Fully rendered prompt string.
            max_new_tokens (int | None): Optional generation token cap override.

        Returns:
            str: Raw decoded generated text output from the model.
        """

        if self._model is None or self._tokenizer is None:
            self.load_model()

        if self.is_mock_mode:
            return self._mock_reference_letter()

        generation_max_tokens = max_new_tokens or self.settings.DOC_GEN_MAX_TOKENS
        try:
            inputs = self._tokenizer(prompt, return_tensors="pt")
            if hasattr(self._model, "device"):
                inputs = {key: value.to(self._model.device) for key, value in inputs.items()}
            output_tokens = self._model.generate(
                **inputs,
                max_new_tokens=generation_max_tokens,
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                do_sample=True,
                repetition_penalty=1.1,
            )
        except Exception as exc:
            raise ModelExecutionError(f"MedGemma 27B inference failed: {exc}") from exc

        decoded_output = self._tokenizer.decode(output_tokens[0], skip_special_tokens=True)
        return self._strip_prompt_prefix(decoded_output, prompt)

    def generate_document(self, transcript: str, context: PatientContext) -> ClinicalDocument:
        """Render prompt, generate text with retry policy, and build ClinicalDocument.

        Args:
            transcript (str): Consultation transcript text.
            context (PatientContext): Structured patient context payload.

        Returns:
            ClinicalDocument: Parsed clinical letter representation with section objects.
        """

        prompt = self._render_prompt(transcript, context)
        generation_start = time.perf_counter()

        last_error: Exception | None = None
        for attempt, token_limit in enumerate((2048, 1024), start=1):
            try:
                generated_text = self.generate(prompt, max_new_tokens=token_limit)
                sections = self._parse_sections(generated_text)
                if len(sections) < 4:
                    raise ValueError("Generated output did not contain enough parseable sections")
                generation_time_s = round(time.perf_counter() - generation_start, 3)
                return self._build_document(context, sections, generation_time_s)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Document generation attempt failed", attempt=attempt, error=str(exc))

        raise ModelExecutionError(f"Document generation failed after retry: {last_error}")

    def _render_prompt(self, transcript: str, context: PatientContext) -> str:
        """Render the document generation Jinja2 template with consultation inputs.

        Args:
            transcript (str): Consultation transcript text.
            context (PatientContext): Structured patient context data.

        Returns:
            str: Rendered prompt string supplied to the language model.
        """

        env = Environment(loader=FileSystemLoader(PROMPTS_DIR))
        template = env.get_template("document_generation.j2")
        context_json = json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2)
        return template.render(
            letter_date=datetime.now(tz=timezone.utc).strftime("%d %b %Y"),
            clinician_name="Dr. Sarah Chen",
            clinician_title="Consultant Diabetologist",
            transcript=transcript,
            context_json=context_json,
        )

    @staticmethod
    def _parse_sections(generated_text: str) -> list[DocumentSection]:
        """Parse generated letter text into section objects using heading detection rules.

        Args:
            generated_text (str): Raw generated letter text.

        Returns:
            list[DocumentSection]: Ordered parsed sections with heading and content fields.
        """

        section_pattern = re.compile(
            r"^(?:\*\*|##\s*)?(History of presenting complaint|Examination findings|Investigation results|Assessment and plan|Current medications)[:\*\s]*$",
            flags=re.IGNORECASE,
        )
        sections: list[DocumentSection] = []
        current_heading: str | None = None
        current_lines: list[str] = []

        for raw_line in generated_text.splitlines():
            line = raw_line.strip()
            heading_match = section_pattern.match(line)
            if heading_match:
                if current_heading and current_lines:
                    sections.append(
                        DocumentSection(
                            heading=current_heading,
                            content="\n".join(current_lines).strip(),
                            editable=True,
                            fhir_sources=[],
                        )
                    )
                current_heading = heading_match.group(1).strip().title()
                current_lines = []
                continue

            if current_heading and line:
                current_lines.append(line)

        if current_heading and current_lines:
            sections.append(
                DocumentSection(
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                    editable=True,
                    fhir_sources=[],
                )
            )

        if not sections:
            sections = [
                DocumentSection(
                    heading=heading,
                    content="Content unavailable in generated output.",
                    editable=True,
                    fhir_sources=[],
                )
                for heading in KNOWN_SECTION_HEADINGS
            ]
        return sections

    @staticmethod
    def _build_document(
        context: PatientContext,
        sections: list[DocumentSection],
        generation_time_s: float,
    ) -> ClinicalDocument:
        """Construct ClinicalDocument schema object from parsed generation outputs.

        Args:
            context (PatientContext): Structured patient context data.
            sections (list[DocumentSection]): Parsed generated document sections.
            generation_time_s (float): Generation wall-clock duration in seconds.

        Returns:
            ClinicalDocument: Final structured letter ready for API response.
        """

        demographics = context.demographics
        patient_name = str(demographics.get("name", "Unknown patient"))
        patient_dob = str(demographics.get("dob", ""))
        nhs_number = str(demographics.get("nhs_number", ""))
        medications_list = [med.get("name", "") for med in context.medications if med.get("name")]

        return ClinicalDocument(
            consultation_id=context.patient_id,
            letter_date=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
            patient_name=patient_name,
            patient_dob=patient_dob,
            nhs_number=nhs_number,
            addressee="GP Practice",
            salutation="Dear Dr.,",
            sections=sections,
            medications_list=medications_list,
            sign_off="Dr. Sarah Chen, Consultant Diabetologist",
            status=ConsultationStatus.REVIEW,
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            generation_time_s=generation_time_s,
            discrepancies=[],
        )

    @staticmethod
    def _strip_prompt_prefix(decoded_output: str, prompt: str) -> str:
        """Remove prompt text prefix when decoder echoes the full prompt + completion.

        Args:
            decoded_output (str): Tokenizer-decoded text from model output ids.
            prompt (str): Original model prompt string.

        Returns:
            str: Completion-only output when prompt prefix is present.
        """

        if decoded_output.startswith(prompt):
            return decoded_output[len(prompt) :].strip()
        return decoded_output.strip()

    @staticmethod
    def _mock_reference_letter() -> str:
        """Return deterministic reference letter text for mock mode generation.

        Args:
            None: Uses embedded fixture text.

        Returns:
            str: Structured letter text with known section headings.
        """

        return (
            "History of presenting complaint\n"
            "Mrs Thompson reported worsening fatigue and reduced exercise tolerance over the last three months. "
            "She confirmed she is taking metformin and gliclazide but occasionally misses evening doses.\n\n"
            "Examination findings\n"
            "No acute distress was described during the consultation. She denied chest pain, syncope, or focal neurological symptoms.\n\n"
            "Investigation results\n"
            "Recent blood results showed HbA1c 55 mmol/mol with eGFR 52 mL/min/1.73m². "
            "Penicillin allergy with previous anaphylaxis was reconfirmed.\n\n"
            "Assessment and plan\n"
            "Overall picture is suboptimal glycaemic control with associated fatigue. Plan is lifestyle reinforcement, medicine adherence review, "
            "repeat renal profile in 3 months, and consideration of treatment escalation if HbA1c remains above target.\n\n"
            "Current medications\n"
            "Metformin 1 g twice daily; Gliclazide 80 mg twice daily."
        )
