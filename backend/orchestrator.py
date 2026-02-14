"""Pipeline orchestrator coordinating transcription, context retrieval, and prompt assembly."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.errors import ModelExecutionError, get_component_logger
from backend.models.ehr_agent import EHRAgent
from backend.models.medasr import MedASRModel
from backend.schemas import Consultation, ConsultationStatus, Patient, PipelineProgress, PipelineStage

logger = get_component_logger("orchestrator")


class PipelineOrchestrator:
    """Coordinate the consultation lifecycle across all model pipeline stages.

    Args:
        medasr_model (MedASRModel | None): Optional MedASR model wrapper instance.
        ehr_agent (EHRAgent | None): Optional EHR agent instance.

    Returns:
        None: Initialises orchestrator state stores in memory.
    """

    def __init__(self, medasr_model: MedASRModel | None = None, ehr_agent: EHRAgent | None = None) -> None:
        self.consultations: dict[str, Consultation] = {}
        self.progress: dict[str, PipelineProgress] = {}
        self._medasr_model = medasr_model or MedASRModel()
        self._ehr_agent = ehr_agent or EHRAgent()

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

        consultation = self.get_consultation(consultation_id)
        if not consultation.audio_file_path:
            raise ModelExecutionError("No uploaded audio available for this consultation")

        consultation.status = ConsultationStatus.PROCESSING
        consultation.ended_at = self._timestamp()

        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.TRANSCRIBING,
            progress_pct=33,
            message="Finalising transcript...",
        )
        transcript = self._medasr_model.transcribe(consultation.audio_file_path)
        consultation.transcript = transcript.model_copy(update={"consultation_id": consultation_id})

        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.RETRIEVING_CONTEXT,
            progress_pct=66,
            message="Synthesising patient context...",
        )
        if consultation.context is None:
            consultation.context = self._ehr_agent.get_patient_context(consultation.patient.id)

        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.GENERATING_DOCUMENT,
            progress_pct=90,
            message="Combining transcript and context for document generation...",
        )
        if consultation.transcript and consultation.context:
            consultation.document = None
            _ = self._build_document_prompt_payload(consultation_id)

        consultation.pipeline_stage = PipelineStage.COMPLETE
        consultation.status = ConsultationStatus.REVIEW
        self.progress[consultation_id] = PipelineProgress(
            consultation_id=consultation_id,
            stage=PipelineStage.COMPLETE,
            progress_pct=100,
            message="Pipeline complete. Ready for document generation.",
        )
        return consultation

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
