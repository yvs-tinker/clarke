"""Mock FHIR API server for local development and fallback deployments."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from loguru import logger

FHIR_BASE_URL = "http://localhost:8080/fhir"
DEFAULT_BUNDLES_DIR = Path(__file__).resolve().parents[2] / "data" / "fhir_bundles"

app = FastAPI(title="Clarke Mock FHIR API", version="1.0.0")


class BundleIndex:
    """In-memory index for patient bundles keyed by patient id and resource type."""

    def __init__(self, bundles_dir: Path) -> None:
        """Initialise and preload all FHIR bundles from disk.

        Args:
            bundles_dir (Path): Directory containing per-patient bundle JSON files.

        Returns:
            None: Instance state is populated in-place.
        """
        self.bundles_dir = bundles_dir
        self.patient_resources: dict[str, dict[str, Any]] = {}
        self.resources_by_type: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self._load_bundles()

    def _load_bundles(self) -> None:
        """Load all bundle files and build lookup indexes for API routes.

        Args:
            None: Uses instance `bundles_dir`.

        Returns:
            None: Internal index maps are rebuilt.
        """
        if not self.bundles_dir.exists():
            logger.bind(component="mock_fhir_api").warning(
                "Bundle directory does not exist", bundles_dir=str(self.bundles_dir)
            )
            return

        for bundle_file in sorted(self.bundles_dir.glob("*.json")):
            with bundle_file.open("r", encoding="utf-8") as file_handle:
                bundle = json.load(file_handle)

            for entry in bundle.get("entry", []):
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType")
                if not resource_type:
                    continue

                patient_id = self._extract_patient_id(resource)
                if not patient_id and resource_type == "Patient":
                    patient_id = resource.get("id")

                if not patient_id:
                    continue

                if resource_type == "Patient":
                    self.patient_resources[patient_id] = resource

                self.resources_by_type.setdefault(resource_type, {}).setdefault(patient_id, []).append(resource)

        logger.bind(component="mock_fhir_api").info(
            "Loaded mock FHIR bundles",
            patients=len(self.patient_resources),
            bundles_dir=str(self.bundles_dir),
        )

    @staticmethod
    def _extract_patient_id(resource: dict[str, Any]) -> str | None:
        """Extract patient identifier from common FHIR reference fields.

        Args:
            resource (dict[str, Any]): A FHIR resource object.

        Returns:
            str | None: Patient id (e.g. `pt-001`) when detectable, otherwise None.
        """
        reference_candidates = [
            resource.get("subject", {}).get("reference"),
            resource.get("patient", {}).get("reference"),
        ]
        for candidate in reference_candidates:
            if candidate and isinstance(candidate, str) and candidate.startswith("Patient/"):
                return candidate.split("/", maxsplit=1)[1]
        return None

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        """Return a single patient resource by id.

        Args:
            patient_id (str): Patient identifier.

        Returns:
            dict[str, Any] | None: Patient resource when present, else None.
        """
        return self.patient_resources.get(patient_id)

    def get_resources(self, resource_type: str, patient_id: str) -> list[dict[str, Any]]:
        """Return all indexed resources of a given type for a patient.

        Args:
            resource_type (str): FHIR resource type name.
            patient_id (str): Patient identifier.

        Returns:
            list[dict[str, Any]]: Matching resources, empty list when none found.
        """
        return self.resources_by_type.get(resource_type, {}).get(patient_id, [])

    def search_patients(self, name_term: str) -> list[dict[str, Any]]:
        """Search patients by case-insensitive name matching across given/family/prefix.

        Args:
            name_term (str): Name fragment entered by caller.

        Returns:
            list[dict[str, Any]]: Matching patient resources.
        """
        lowered = name_term.lower().strip()
        matches: list[dict[str, Any]] = []
        for patient in self.patient_resources.values():
            for name in patient.get("name", []):
                tokens = []
                tokens.extend(name.get("prefix", []))
                tokens.extend(name.get("given", []))
                if family := name.get("family"):
                    tokens.append(family)
                if any(lowered in str(token).lower() for token in tokens):
                    matches.append(patient)
                    break
        return matches


BUNDLE_INDEX = BundleIndex(Path(os.getenv("MOCK_FHIR_BUNDLES_DIR", str(DEFAULT_BUNDLES_DIR))))


def build_search_bundle(resource_type: str, resources: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a FHIR searchset bundle payload from resource rows.

    Args:
        resource_type (str): Resource type represented in `resources`.
        resources (list[dict[str, Any]]): FHIR resources to include.

    Returns:
        dict[str, Any]: FHIR Bundle with `entry` and `total` fields.
    """
    entries = [
        {
            "fullUrl": f"{FHIR_BASE_URL}/{resource_type}/{resource.get('id', '')}",
            "resource": resource,
        }
        for resource in resources
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": entries,
    }


def get_effective_sort_key(resource: dict[str, Any]) -> str:
    """Resolve date-like sort key for FHIR resources supporting `_sort=-date`.

    Args:
        resource (dict[str, Any]): Resource candidate.

    Returns:
        str: Date-like string usable for lexicographic descending sort.
    """
    return (
        resource.get("effectiveDateTime")
        or resource.get("issued")
        or resource.get("authoredOn")
        or resource.get("onsetDateTime")
        or resource.get("period", {}).get("start")
        or ""
    )


def get_patient_or_404(patient_id: str) -> dict[str, Any]:
    """Resolve patient resource or raise a 404 HTTP exception.

    Args:
        patient_id (str): Patient identifier to lookup.

    Returns:
        dict[str, Any]: Existing patient resource.
    """
    patient_resource = BUNDLE_INDEX.get_patient(patient_id)
    if not patient_resource:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")
    return patient_resource


@app.get("/fhir/Patient/{patient_id}")
async def read_patient(patient_id: str) -> dict[str, Any]:
    """Return a Patient resource by id.

    Args:
        patient_id (str): Patient identifier path parameter.

    Returns:
        dict[str, Any]: Patient resource payload.
    """
    return get_patient_or_404(patient_id)


@app.get("/fhir/Patient")
async def search_patient(name: str = Query(default=""), _count: int = Query(default=10, ge=1)) -> dict[str, Any]:
    """Search patients by name and return a FHIR searchset bundle.

    Args:
        name (str): Name fragment for case-insensitive matching.
        _count (int): Maximum result size.

    Returns:
        dict[str, Any]: Search bundle of Patient resources.
    """
    resources = BUNDLE_INDEX.search_patients(name) if name else list(BUNDLE_INDEX.patient_resources.values())
    return build_search_bundle("Patient", resources[:_count])


def list_patient_resources(resource_type: str, patient: str, limit: int, sort_desc_by_date: bool = False) -> dict[str, Any]:
    """Fetch filtered patient resources and wrap them as a searchset bundle.

    Args:
        resource_type (str): FHIR resource type to return.
        patient (str): Patient identifier.
        limit (int): Maximum number of resources to include.
        sort_desc_by_date (bool): Whether to sort descending by date-like fields.

    Returns:
        dict[str, Any]: Search bundle for the requested resource type.
    """
    get_patient_or_404(patient)
    resources = list(BUNDLE_INDEX.get_resources(resource_type, patient))
    if sort_desc_by_date:
        resources.sort(key=get_effective_sort_key, reverse=True)
    return build_search_bundle(resource_type, resources[:limit])


@app.get("/fhir/Condition")
async def list_conditions(
    patient: str,
    clinical_status: str | None = Query(default=None, alias="clinical-status"),
    _count: int = Query(default=20, ge=1),
) -> dict[str, Any]:
    """List Condition resources for a patient with optional active-status filtering.

    Args:
        patient (str): Patient identifier query parameter.
        clinical_status (str | None): Optional status filter (e.g. `active`).
        _count (int): Maximum number of rows.

    Returns:
        dict[str, Any]: Condition search bundle.
    """
    bundle = list_patient_resources("Condition", patient, _count)
    if clinical_status:
        filtered_entries = [
            item
            for item in bundle["entry"]
            if any(
                coding.get("code") == clinical_status
                for coding in item["resource"].get("clinicalStatus", {}).get("coding", [])
            )
        ]
        bundle["entry"] = filtered_entries
        bundle["total"] = len(filtered_entries)
    return bundle


@app.get("/fhir/MedicationRequest")
async def list_medication_requests(
    patient: str,
    status: str | None = Query(default=None),
    _count: int = Query(default=20, ge=1),
) -> dict[str, Any]:
    """List MedicationRequest resources for a patient with optional status filter.

    Args:
        patient (str): Patient identifier query parameter.
        status (str | None): Optional medication status filter.
        _count (int): Maximum number of rows.

    Returns:
        dict[str, Any]: MedicationRequest search bundle.
    """
    bundle = list_patient_resources("MedicationRequest", patient, _count, sort_desc_by_date=True)
    if status:
        filtered_entries = [item for item in bundle["entry"] if item["resource"].get("status") == status]
        bundle["entry"] = filtered_entries
        bundle["total"] = len(filtered_entries)
    return bundle


@app.get("/fhir/Observation")
async def list_observations(
    patient: str,
    category: str | None = Query(default=None),
    _sort: str | None = Query(default=None),
    _count: int = Query(default=20, ge=1),
) -> dict[str, Any]:
    """List Observation resources for a patient with category/count/sort controls.

    Args:
        patient (str): Patient identifier query parameter.
        category (str | None): Optional observation category code.
        _sort (str | None): Optional sort string (`-date` expected).
        _count (int): Maximum number of rows.

    Returns:
        dict[str, Any]: Observation search bundle.
    """
    sort_desc_by_date = _sort == "-date"
    bundle = list_patient_resources("Observation", patient, _count, sort_desc_by_date=sort_desc_by_date)
    if category:
        filtered_entries = [
            item
            for item in bundle["entry"]
            if any(
                coding.get("code") == category
                for block in item["resource"].get("category", [])
                for coding in block.get("coding", [])
            )
        ]
        bundle["entry"] = filtered_entries
        bundle["total"] = len(filtered_entries)
    return bundle


@app.get("/fhir/AllergyIntolerance")
async def list_allergies(patient: str, _count: int = Query(default=20, ge=1)) -> dict[str, Any]:
    """List AllergyIntolerance resources for a patient.

    Args:
        patient (str): Patient identifier query parameter.
        _count (int): Maximum number of rows.

    Returns:
        dict[str, Any]: AllergyIntolerance search bundle.
    """
    return list_patient_resources("AllergyIntolerance", patient, _count)


@app.get("/fhir/DiagnosticReport")
async def list_diagnostic_reports(
    patient: str,
    _sort: str | None = Query(default=None),
    _count: int = Query(default=5, ge=1),
) -> dict[str, Any]:
    """List DiagnosticReport resources for a patient with optional date sorting.

    Args:
        patient (str): Patient identifier query parameter.
        _sort (str | None): Optional sort string (`-date` expected).
        _count (int): Maximum number of rows.

    Returns:
        dict[str, Any]: DiagnosticReport search bundle.
    """
    return list_patient_resources("DiagnosticReport", patient, _count, sort_desc_by_date=_sort == "-date")


@app.get("/fhir/Encounter")
async def list_encounters(
    patient: str,
    _sort: str | None = Query(default=None),
    _count: int = Query(default=3, ge=1),
) -> dict[str, Any]:
    """List Encounter resources for a patient with optional date sorting.

    Args:
        patient (str): Patient identifier query parameter.
        _sort (str | None): Optional sort string (`-date` expected).
        _count (int): Maximum number of rows.

    Returns:
        dict[str, Any]: Encounter search bundle.
    """
    return list_patient_resources("Encounter", patient, _count, sort_desc_by_date=_sort == "-date")


def main() -> None:
    """Run the mock FHIR API server.

    Args:
        None: Reads host/port from environment variables.

    Returns:
        None: Starts uvicorn process.
    """
    host = os.getenv("MOCK_FHIR_HOST", "0.0.0.0")
    port = int(os.getenv("MOCK_FHIR_PORT", "8080"))
    uvicorn.run("backend.fhir.mock_api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
