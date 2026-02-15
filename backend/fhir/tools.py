"""FHIR tool-call wrappers that extract resources from bundle responses."""

from __future__ import annotations

from typing import Any

from backend.fhir.client import DEFAULT_FHIR_CLIENT


def _bundle_entries(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract resource rows from a FHIR Bundle payload.

    Args:
        bundle (dict[str, Any]): Raw FHIR Bundle response.

    Returns:
        list[dict[str, Any]]: Resource dictionaries found in bundle entries.
    """

    entries = bundle.get("entry", []) if isinstance(bundle, dict) else []
    return [item.get("resource", {}) for item in entries if isinstance(item, dict) and isinstance(item.get("resource"), dict)]


async def search_patients(name: str) -> list[dict[str, Any]]:
    """Search patient resources by name.

    Args:
        name (str): Name term for patient search.

    Returns:
        list[dict[str, Any]]: Matching Patient resources.
    """

    response = await DEFAULT_FHIR_CLIENT.search_patients(name=name)
    return _bundle_entries(response)


async def get_conditions(patient_id: str) -> list[dict[str, Any]]:
    """Return active condition resources for a patient.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        list[dict[str, Any]]: Condition resources.
    """

    response = await DEFAULT_FHIR_CLIENT.get_conditions(patient_id=patient_id)
    return _bundle_entries(response)


async def get_medications(patient_id: str) -> list[dict[str, Any]]:
    """Return active medication request resources for a patient.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        list[dict[str, Any]]: MedicationRequest resources.
    """

    response = await DEFAULT_FHIR_CLIENT.get_medications(patient_id=patient_id)
    return _bundle_entries(response)


async def get_observations(patient_id: str, category: str = "laboratory") -> list[dict[str, Any]]:
    """Return observation resources for a patient and category.

    Args:
        patient_id (str): Patient identifier.
        category (str): Observation category code.

    Returns:
        list[dict[str, Any]]: Observation resources.
    """

    response = await DEFAULT_FHIR_CLIENT.get_observations(patient_id=patient_id, category=category)
    return _bundle_entries(response)


async def get_allergies(patient_id: str) -> list[dict[str, Any]]:
    """Return allergy resources for a patient.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        list[dict[str, Any]]: AllergyIntolerance resources.
    """

    response = await DEFAULT_FHIR_CLIENT.get_allergies(patient_id=patient_id)
    return _bundle_entries(response)


async def get_diagnostic_reports(patient_id: str) -> list[dict[str, Any]]:
    """Return diagnostic report resources for a patient.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        list[dict[str, Any]]: DiagnosticReport resources.
    """

    response = await DEFAULT_FHIR_CLIENT.get_diagnostic_reports(patient_id=patient_id)
    return _bundle_entries(response)


async def get_recent_encounters(patient_id: str) -> list[dict[str, Any]]:
    """Return recent encounter resources for a patient.

    Args:
        patient_id (str): Patient identifier.

    Returns:
        list[dict[str, Any]]: Encounter resources.
    """

    response = await DEFAULT_FHIR_CLIENT.get_recent_encounters(patient_id=patient_id)
    return _bundle_entries(response)
