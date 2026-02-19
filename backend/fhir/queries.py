"""Deterministic FHIR query aggregation used as EHR fallback context retrieval."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.fhir.client import DEFAULT_FHIR_CLIENT
from backend.fhir.tools import (
    get_allergies,
    get_conditions,
    get_diagnostic_reports,
    get_medications,
    get_observations,
    get_recent_encounters,
    search_patients,
)


async def get_full_patient_context(patient_id: str) -> dict[str, Any]:
    """Aggregate all FHIR tool outputs for deterministic patient context assembly.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        dict[str, Any]: Aggregated context containing all seven tool result sections.
    """

    (
        patients,
        conditions,
        medications,
        observations,
        allergies,
        diagnostic_reports,
        encounters,
    ) = await asyncio.gather(
        search_patients(patient_id),
        get_conditions(patient_id),
        get_medications(patient_id),
        get_observations(patient_id),
        get_allergies(patient_id),
        get_diagnostic_reports(patient_id),
        get_recent_encounters(patient_id),
    )

    if not patients:
        patient_resource = await DEFAULT_FHIR_CLIENT.get_patient(patient_id)
        if patient_resource:
            patients = [patient_resource]

    return {
        "patient_id": patient_id,
        "patients": patients,
        "conditions": conditions,
        "medications": medications,
        "observations": observations,
        "allergies": allergies,
        "diagnostic_reports": diagnostic_reports,
        "encounters": encounters,
    }
