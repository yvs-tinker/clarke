"""Asynchronous FHIR REST client for retrieving patient-scoped resources."""

from __future__ import annotations

from typing import Any

import httpx

from backend.config import get_settings
from backend.errors import FHIRClientError, get_component_logger

logger = get_component_logger("fhir_client")


class FHIRClient:
    """HTTP client for FHIR query patterns used by Clarke orchestration.

    Args:
        fhir_server_url (str): Base URL of FHIR API including `/fhir` path.
        timeout_s (int): Request timeout in seconds.

    Returns:
        None: Initialises a client instance.
    """

    def __init__(self, fhir_server_url: str, timeout_s: int) -> None:
        self.fhir_server_url = fhir_server_url.rstrip("/")
        self.timeout_s = timeout_s

    async def _request_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GET request with timeout, 404-empty behaviour, and one 5xx retry.

        Args:
            path (str): FHIR relative path beginning with `/`.
            params (dict[str, Any] | None): Query parameters for the request.

        Returns:
            dict[str, Any]: Parsed JSON response, or empty dictionary for 404 responses.
        """

        url = f"{self.fhir_server_url}{path}"
        attempts = 0
        while attempts < 2:
            attempts += 1
            try:
                async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                    response = await client.get(url, params=params)
            except httpx.TimeoutException as exc:
                logger.error("FHIR request timed out", url=url, params=params, timeout_s=self.timeout_s)
                raise FHIRClientError(
                    f"FHIR timeout for {url} with params={params} after {self.timeout_s}s"
                ) from exc
            except httpx.HTTPError as exc:
                logger.error("FHIR transport error", url=url, params=params, error=str(exc))
                raise FHIRClientError(f"FHIR transport error for {url}: {exc}") from exc

            if response.status_code == 404:
                return {}

            if response.status_code >= 500 and attempts < 2:
                logger.warning("FHIR server 5xx, retrying once", url=url, status_code=response.status_code)
                continue

            if response.status_code >= 400:
                raise FHIRClientError(
                    f"FHIR request failed for {url} status={response.status_code} body={response.text}"
                )

            return response.json()

        raise FHIRClientError(f"FHIR server error persisted after retry for {url}")

    async def get_patient(self, patient_id: str) -> dict[str, Any]:
        """Fetch a Patient resource by id.

        Args:
            patient_id (str): Patient identifier.

        Returns:
            dict[str, Any]: Patient JSON resource or empty dict when not found.
        """

        return await self._request_json(f"/Patient/{patient_id}")

    async def search_patients(self, name: str, count: int = 10) -> dict[str, Any]:
        """Search patients by name using FHIR Patient endpoint.

        Args:
            name (str): Name fragment to search.
            count (int): Maximum number of records to request.

        Returns:
            dict[str, Any]: FHIR Bundle search response.
        """

        return await self._request_json("/Patient", params={"name": name, "_count": count})

    async def get_conditions(self, patient_id: str, clinical_status: str = "active") -> dict[str, Any]:
        """Fetch Condition resources for a patient.

        Args:
            patient_id (str): Patient identifier.
            clinical_status (str): Desired clinical status value.

        Returns:
            dict[str, Any]: FHIR Bundle response.
        """

        return await self._request_json(
            "/Condition", params={"patient": patient_id, "clinical-status": clinical_status}
        )

    async def get_medications(self, patient_id: str, status: str = "active") -> dict[str, Any]:
        """Fetch MedicationRequest resources for a patient.

        Args:
            patient_id (str): Patient identifier.
            status (str): Medication status filter.

        Returns:
            dict[str, Any]: FHIR Bundle response.
        """

        return await self._request_json("/MedicationRequest", params={"patient": patient_id, "status": status})

    async def get_observations(
        self,
        patient_id: str,
        category: str = "laboratory",
        sort: str = "-date",
        count: int = 20,
    ) -> dict[str, Any]:
        """Fetch Observation resources for a patient.

        Args:
            patient_id (str): Patient identifier.
            category (str): Observation category code filter.
            sort (str): Sort directive for date-like fields.
            count (int): Maximum number of records.

        Returns:
            dict[str, Any]: FHIR Bundle response.
        """

        return await self._request_json(
            "/Observation",
            params={"patient": patient_id, "category": category, "_sort": sort, "_count": count},
        )

    async def get_allergies(self, patient_id: str) -> dict[str, Any]:
        """Fetch AllergyIntolerance resources for a patient.

        Args:
            patient_id (str): Patient identifier.

        Returns:
            dict[str, Any]: FHIR Bundle response.
        """

        return await self._request_json("/AllergyIntolerance", params={"patient": patient_id})

    async def get_diagnostic_reports(self, patient_id: str, sort: str = "-date", count: int = 5) -> dict[str, Any]:
        """Fetch DiagnosticReport resources for a patient.

        Args:
            patient_id (str): Patient identifier.
            sort (str): Sort directive for date-like fields.
            count (int): Maximum number of records.

        Returns:
            dict[str, Any]: FHIR Bundle response.
        """

        return await self._request_json(
            "/DiagnosticReport", params={"patient": patient_id, "_sort": sort, "_count": count}
        )

    async def get_recent_encounters(self, patient_id: str, sort: str = "-date", count: int = 3) -> dict[str, Any]:
        """Fetch recent Encounter resources for a patient.

        Args:
            patient_id (str): Patient identifier.
            sort (str): Sort directive for date-like fields.
            count (int): Maximum number of records.

        Returns:
            dict[str, Any]: FHIR Bundle response.
        """

        return await self._request_json("/Encounter", params={"patient": patient_id, "_sort": sort, "_count": count})


settings = get_settings()
DEFAULT_FHIR_CLIENT = FHIRClient(fhir_server_url=settings.FHIR_SERVER_URL, timeout_s=settings.FHIR_TIMEOUT_S)
