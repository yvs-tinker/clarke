"""Pipeline orchestrator coordinating transcription, context retrieval, and prompt assembly."""

from __future__ import annotations

import json
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import torch

from backend.errors import ModelExecutionError, get_component_logger
from backend.audio import validate_audio
from backend.models.doc_generator import DocumentGenerator
from backend.models.ehr_agent import EHRAgent
from backend.models.medasr import MedASRModel
from backend.schemas import ClinicalDocument, Consultation, ConsultationStatus, Patient, PatientContext, PipelineProgress, PipelineStage

logger = get_component_logger("orchestrator")


class PipelineOrchestrator:
    """Coordinate the consultation lifecycle across all model pipeline stages.

    Args:
        medasr_model (MedASRModel | None): Optional MedASR model wrapper instance.
        ehr_agent (EHRAgent | None): Optional EHR agent instance.

    Returns:
        None: Initialises orchestrator state stores in memory.
    """

    def __init__(
        self,
        medasr_model: MedASRModel | None = None,
        ehr_agent: EHRAgent | None = None,
        doc_generator: DocumentGenerator | None = None,
    ) -> None:
        self.consultations: dict[str, Consultation] = {}
        self.progress: dict[str, PipelineProgress] = {}
        self._medasr_model = medasr_model or MedASRModel()
        self._ehr_agent = ehr_agent or EHRAgent()
        self._doc_generator = doc_generator or DocumentGenerator()

    @staticmethod
    def _clear_cuda_cache() -> None:
        """Release cached CUDA memory between heavy model stages when CUDA is available.

        Args:
            None: Uses current torch CUDA runtime state.

        Returns:
            None: Performs in-place cache cleanup only.
        """

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def _timestamp() -> str:
        """Return current UTC timestamp string for consultation lifecycle fields.

        Args:
            None: Reads current clock only.

        Returns:
            str: ISO timestamp with timezone.
        """

        return datetime.now(tz=timezone.utc).isoformat()

    def start_consultation(self, patient: Patient) -> Consultation:
        """Create and store a consultation in recording state.

        Args:
            patient (Patient): Patient selected for this consultation.

        Returns:
            Consultation: Newly created consultation object.
        """

        consultation_id = f"cons-{uuid4()}"
        consultation = Consultation(
            id=consultation_id,
            patient=patient,
            status=ConsultationStatus.RECORDING,
            started_at=self._timestamp(),
        )
        self.consultations[consultation_id] = consultation
        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.RETRIEVING_CONTEXT,
            progress_pct=5,
            message="Consultation started. Recording in progress.",
        )
        return consultation

    def prefetch_context(self, consultation_id: str) -> None:
        """Preload patient context for a consultation to reduce end-stage latency.

        Args:
            consultation_id (str): Consultation identifier.

        Returns:
            None: Updates consultation context cache in place.
        """

        consultation = self.get_consultation(consultation_id)
        if consultation.context is not None:
            return

        try:
            consultation.context = self._ehr_agent.get_patient_context(consultation.patient.id)
            self.progress[consultation_id] = PipelineProgress(
                consultation_id=consultation_id,
                stage=PipelineStage.RETRIEVING_CONTEXT,
                progress_pct=25,
                message="Patient context prefetched.",
            )
        except Exception as exc:
            logger.warning("Context prefetch failed", consultation_id=consultation_id, error=str(exc))

    def end_consultation(self, consultation_id: str) -> Consultation:
        """Finalize recording and run the staged processing pipeline.

        Args:
            consultation_id (str): Consultation identifier.

        Returns:
            Consultation: Updated consultation after pipeline completion.
        """

        try:
            return asyncio.run(
                asyncio.wait_for(
                    asyncio.to_thread(self._run_pipeline, consultation_id),
                    timeout=float(self._doc_generator.settings.PIPELINE_TIMEOUT_S),
                )
            )
        except TimeoutError:
            raise
        except asyncio.TimeoutError as exc:
            raise TimeoutError("Pipeline timed out") from exc

    def _run_pipeline(self, consultation_id: str) -> Consultation:
        """Execute all pipeline stages for an existing consultation.

        Args:
            consultation_id (str): Consultation identifier.

        Returns:
            Consultation: Updated consultation after pipeline completion.
        """

        consultation = self.get_consultation(consultation_id)
        if not consultation.audio_file_path:
            raise ModelExecutionError("No uploaded audio available for this consultation")

        validate_audio(consultation.audio_file_path)

        total_start = time.perf_counter()
        stage_start = time.perf_counter()
        consultation.status = ConsultationStatus.PROCESSING
        consultation.ended_at = self._timestamp()

        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.TRANSCRIBING,
            progress_pct=33,
            message="Finalising transcript...",
        )
        transcript = self._medasr_model.transcribe(consultation.audio_file_path)
        if not transcript.text.strip():
            raise ModelExecutionError("Audio could not be transcribed.")
        consultation.transcript = transcript.model_copy(update={"consultation_id": consultation_id})
        transcribe_s = round(time.perf_counter() - stage_start, 3)
        logger.info("Pipeline stage complete", consultation_id=consultation_id, stage="transcribe", duration_s=transcribe_s)
        self._clear_cuda_cache()

        stage_start = time.perf_counter()
        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.RETRIEVING_CONTEXT,
            progress_pct=66,
            message="Synthesising patient context...",
        )
        if consultation.context is None:
            try:
                consultation.context = self._ehr_agent.get_patient_context(consultation.patient.id)
            except Exception as exc:
                warning = f"FHIR retrieval unavailable; continuing with transcript only: {exc}"
                logger.warning("FHIR degradation activated", consultation_id=consultation_id, warning=warning)
                consultation.context = self._build_transcript_only_context(consultation, warning)
        context_s = round(time.perf_counter() - stage_start, 3)
        logger.info("Pipeline stage complete", consultation_id=consultation_id, stage="retrieve_context", duration_s=context_s)
        self._clear_cuda_cache()

        stage_start = time.perf_counter()
        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.GENERATING_DOCUMENT,
            progress_pct=90,
            message="Combining transcript and context for document generation...",
        )
        if consultation.transcript and consultation.context:
            consultation.context = self._truncate_context(consultation.context)
            consultation.document = self._generate_document_with_oom_retry(
                consultation.transcript.text,
                consultation.context,
                consultation_id,
            ).model_copy(update={"consultation_id": consultation_id})
        else:
            raise ModelExecutionError("Transcript and patient context are required before document generation")
        generate_s = round(time.perf_counter() - stage_start, 3)
        logger.info("Pipeline stage complete", consultation_id=consultation_id, stage="generate_document", duration_s=generate_s)
        self._clear_cuda_cache()

        consultation.pipeline_stage = PipelineStage.COMPLETE
        consultation.status = ConsultationStatus.REVIEW
        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.COMPLETE,
            progress_pct=100,
            message="Pipeline complete. Clinical document ready for review.",
        )
        total_s = round(time.perf_counter() - total_start, 3)
        logger.info(
            "Pipeline completed",
            consultation_id=consultation_id,
            total_duration_s=total_s,
            transcribe_s=transcribe_s,
            context_s=context_s,
            generate_s=generate_s,
        )
        return consultation

    def _generate_document_with_oom_retry(
        self,
        transcript_text: str,
        context: PatientContext,
        consultation_id: str,
    ) -> ClinicalDocument:
        """Generate a document with one OOM recovery retry.

        Args:
            transcript_text (str): Consultation transcript text.
            context (PatientContext): Context payload for document generation.
            consultation_id (str): Consultation identifier for logging.

        Returns:
            ClinicalDocument: Generated document payload.
        """

        max_tokens = int(self._doc_generator.settings.DOC_GEN_MAX_TOKENS)
        try:
            return self._doc_generator.generate_document(transcript_text, context, max_new_tokens=max_tokens)
        except torch.cuda.OutOfMemoryError as exc:
            self._clear_cuda_cache()
            reduced_tokens = max(256, max_tokens // 2)
            logger.warning(
                "OOM during document generation; retrying with reduced token budget",
                consultation_id=consultation_id,
                previous_max_new_tokens=max_tokens,
                retry_max_new_tokens=reduced_tokens,
            )
            return self._doc_generator.generate_document(transcript_text, context, max_new_tokens=reduced_tokens)

    def _build_transcript_only_context(self, consultation: Consultation, warning: str) -> PatientContext:
        """Build minimal patient context when EHR retrieval fails.

        Args:
            consultation (Consultation): Consultation containing patient demographics.
            warning (str): Retrieval warning text to persist.

        Returns:
            PatientContext: Transcript-only fallback context.
        """

        return PatientContext(
            patient_id=consultation.patient.id,
            demographics={
                "name": consultation.patient.name,
                "dob": consultation.patient.date_of_birth,
                "nhs_number": consultation.patient.nhs_number,
                "age": consultation.patient.age,
                "sex": consultation.patient.sex,
            },
            problem_list=[],
            medications=[],
            allergies=[],
            recent_labs=[],
            recent_imaging=[],
            clinical_flags=[],
            last_letter_excerpt=None,
            retrieval_warnings=[warning],
            retrieved_at=self._timestamp(),
        )

    def _truncate_context(self, context: PatientContext) -> PatientContext:
        """Truncate oversized context payloads to fit the max-sequence envelope.

        Args:
            context (PatientContext): Structured patient context before generation.

        Returns:
            PatientContext: Potentially truncated context payload.
        """

        max_tokens = int(self._doc_generator.settings.MAX_SEQ_LENGTH)
        context_payload = context.model_dump(mode="json")
        estimated_tokens = len(json.dumps(context_payload, ensure_ascii=False).split())
        if estimated_tokens <= max_tokens:
            return context

        for list_field in ("recent_labs", "medications", "problem_list", "allergies", "recent_imaging", "clinical_flags"):
            values = context_payload.get(list_field, [])
            if isinstance(values, list) and len(values) > 2:
                context_payload[list_field] = values[: max(2, len(values) // 2)]
            estimated_tokens = len(json.dumps(context_payload, ensure_ascii=False).split())
            if estimated_tokens <= max_tokens:
                break

        warnings = list(context_payload.get("retrieval_warnings", []))
        warnings.append("Context exceeded token budget and was truncated to fit generation limits.")
        context_payload["retrieval_warnings"] = warnings
        return PatientContext.model_validate(context_payload)

    def sign_off_document(self, consultation_id: str) -> ClinicalDocument:
        """Mark a generated consultation document as signed off.

        Args:
            consultation_id (str): Consultation identifier.

        Returns:
            ClinicalDocument: Signed-off document for the consultation.
        """

        consultation = self.get_consultation(consultation_id)
        if consultation.document is None:
            raise ModelExecutionError("No generated document available to sign off")

        consultation.status = ConsultationStatus.SIGNED_OFF
        consultation.document = consultation.document.model_copy(update={"status": ConsultationStatus.SIGNED_OFF})
        logger.info("Document signed off", consultation_id=consultation_id)
        return consultation.document

    def regenerate_document_section(self, consultation_id: str, section_heading: str) -> ClinicalDocument:
        """Regenerate a single section by re-running generation and replacing matching heading content.

        Args:
            consultation_id (str): Consultation identifier.
            section_heading (str): Heading name for the section to regenerate.

        Returns:
            ClinicalDocument: Updated clinical document with refreshed section content.
        """

        consultation = self.get_consultation(consultation_id)
        if consultation.transcript is None or consultation.context is None:
            raise ModelExecutionError("Transcript and context are required to regenerate a section")
        if consultation.document is None:
            raise ModelExecutionError("No generated document available to regenerate")

        refreshed_document = self._doc_generator.generate_document(
            consultation.transcript.text,
            consultation.context,
        ).model_copy(update={"consultation_id": consultation_id})
        replacement_section = next(
            (
                section
                for section in refreshed_document.sections
                if section.heading.lower() == section_heading.strip().lower()
            ),
            None,
        )
        if replacement_section is None:
            raise ModelExecutionError(f"Section not found in regenerated output: {section_heading}")

        updated_sections = []
        replaced = False
        for section in consultation.document.sections:
            if section.heading.lower() == section_heading.strip().lower():
                updated_sections.append(replacement_section)
                replaced = True
            else:
                updated_sections.append(section)

        if not replaced:
            raise ModelExecutionError(f"Section not found in existing document: {section_heading}")

        consultation.document = consultation.document.model_copy(
            update={
                "sections": updated_sections,
                "generated_at": refreshed_document.generated_at,
                "generation_time_s": refreshed_document.generation_time_s,
                "status": ConsultationStatus.REVIEW,
            }
        )
        consultation.status = ConsultationStatus.REVIEW
        logger.info("Document section regenerated", consultation_id=consultation_id, section_heading=section_heading)
        return consultation.document

    def _build_document_prompt_payload(self, consultation_id: str) -> str:
        """Compose stage-3 prompt payload from transcript and context as JSON.

        Args:
            consultation_id (str): Consultation identifier.

        Returns:
            str: Combined payload string for downstream document generation model.
        """

        consultation = self.get_consultation(consultation_id)
        if consultation.transcript is None or consultation.context is None:
            raise ModelExecutionError("Transcript and context are required for prompt assembly")

        payload = {
            "consultation_id": consultation_id,
            "transcript": consultation.transcript.text,
            "context": consultation.context.model_dump(mode="json"),
        }
        return json.dumps(payload, ensure_ascii=False)

    def get_consultation(self, consultation_id: str) -> Consultation:
        """Get a consultation by id from in-memory store.

        Args:
            consultation_id (str): Consultation identifier.

        Returns:
            Consultation: Stored consultation object.
        """

        consultation = self.consultations.get(consultation_id)
        if consultation is None:
            raise KeyError(f"Consultation not found: {consultation_id}")
        return consultation

    def get_progress(self, consultation_id: str) -> PipelineProgress:
        """Get latest pipeline progress for a consultation.

        Args:
            consultation_id (str): Consultation identifier.

        Returns:
            PipelineProgress: Last recorded progress event.
        """

        progress = self.progress.get(consultation_id)
        if progress is None:
            raise KeyError(f"Progress not found for consultation: {consultation_id}")
        return progress


PROMPTS_DIR = Path("backend/prompts")
