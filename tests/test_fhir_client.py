"""Tests for Clarke mock FHIR API endpoint behaviour."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.fhir import mock_api


def _write_patient_bundle(bundles_dir: Path) -> None:
    """Create deterministic fixture bundle for endpoint verification.

    Args:
        bundles_dir (Path): Destination directory for fixture bundle file.

    Returns:
        None: Writes a single JSON bundle to disk.
    """
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "pt-001",
                    "identifier": [
                        {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "9434765829",
                        }
                    ],
                    "name": [
                        {
                            "prefix": ["Mrs"],
                            "given": ["Margaret"],
                            "family": "Thompson",
                        }
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-1",
                    "subject": {"reference": "Patient/pt-001"},
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "code": {"text": "Type 2 diabetes mellitus"},
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-2",
                    "subject": {"reference": "Patient/pt-001"},
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "code": {"text": "Chronic kidney disease"},
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-1",
                    "subject": {"reference": "Patient/pt-001"},
                    "status": "active",
                    "authoredOn": "2026-01-02",
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-2",
                    "subject": {"reference": "Patient/pt-001"},
                    "status": "active",
                    "authoredOn": "2026-01-04",
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-1",
                    "subject": {"reference": "Patient/pt-001"},
                    "category": [{"coding": [{"code": "laboratory"}]}],
                    "effectiveDateTime": "2026-01-05",
                    "code": {"text": "HbA1c"},
                    "valueQuantity": {"value": 55, "unit": "mmol/mol"},
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-2",
                    "subject": {"reference": "Patient/pt-001"},
                    "category": [{"coding": [{"code": "laboratory"}]}],
                    "effectiveDateTime": "2026-01-01",
                    "code": {"text": "eGFR"},
                }
            },
            {
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": "allergy-1",
                    "patient": {"reference": "Patient/pt-001"},
                    "code": {"text": "Penicillin"},
                }
            },
            {
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": "report-1",
                    "subject": {"reference": "Patient/pt-001"},
                    "effectiveDateTime": "2026-01-07",
                }
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-1",
                    "subject": {"reference": "Patient/pt-001"},
                    "period": {"start": "2026-01-06"},
                }
            },
        ],
    }
    bundles_dir.mkdir(parents=True, exist_ok=True)
    (bundles_dir / "pt-001.json").write_text(json.dumps(bundle), encoding="utf-8")


def _build_test_client(tmp_path: Path) -> TestClient:
    """Construct a test client with BundleIndex pointed at test fixture data.

    Args:
        tmp_path (Path): Temporary path provided by pytest.

    Returns:
        TestClient: FastAPI test client bound to the mock API app.
    """
    bundles_dir = tmp_path / "fhir_bundles"
    _write_patient_bundle(bundles_dir)
    mock_api.BUNDLE_INDEX = mock_api.BundleIndex(bundles_dir)
    return TestClient(mock_api.app)


def test_patient_and_search_endpoints(tmp_path: Path) -> None:
    """Verify Patient by-id and by-name endpoints return expected FHIR payloads.

    Args:
        tmp_path (Path): Temporary filesystem root for fixture bundle files.

    Returns:
        None: Assertions validate endpoint responses.
    """
    client = _build_test_client(tmp_path)

    patient_response = client.get("/fhir/Patient/pt-001")
    assert patient_response.status_code == 200
    assert patient_response.json()["resourceType"] == "Patient"

    search_response = client.get("/fhir/Patient", params={"name": "thompson", "_count": 10})
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["resourceType"] == "Bundle"
    assert payload["total"] == 1


def test_resource_endpoints_filter_sort_and_count(tmp_path: Path) -> None:
    """Verify query filters and sorting semantics across FHIR resource endpoints.

    Args:
        tmp_path (Path): Temporary filesystem root for fixture bundle files.

    Returns:
        None: Assertions validate filtering, count limits, and date sort behaviour.
    """
    client = _build_test_client(tmp_path)

    condition_response = client.get("/fhir/Condition", params={"patient": "pt-001", "clinical-status": "active"})
    assert condition_response.status_code == 200
    assert condition_response.json()["total"] >= 2

    med_response = client.get("/fhir/MedicationRequest", params={"patient": "pt-001", "status": "active", "_count": 1})
    assert med_response.status_code == 200
    assert med_response.json()["total"] == 1

    obs_response = client.get(
        "/fhir/Observation",
        params={"patient": "pt-001", "category": "laboratory", "_sort": "-date", "_count": 20},
    )
    assert obs_response.status_code == 200
    obs_entries = obs_response.json()["entry"]
    assert obs_entries[0]["resource"]["id"] == "obs-1"

    allergy_response = client.get("/fhir/AllergyIntolerance", params={"patient": "pt-001"})
    assert allergy_response.status_code == 200
    assert allergy_response.json()["total"] == 1

    report_response = client.get("/fhir/DiagnosticReport", params={"patient": "pt-001", "_sort": "-date", "_count": 5})
    assert report_response.status_code == 200

    encounter_response = client.get("/fhir/Encounter", params={"patient": "pt-001", "_sort": "-date", "_count": 3})
    assert encounter_response.status_code == 200


def test_unknown_patient_behaviour(tmp_path: Path) -> None:
    """Verify unknown patients return a 404 for patient-scoped endpoints.

    Args:
        tmp_path (Path): Temporary filesystem root for fixture bundle files.

    Returns:
        None: Assertions validate expected 404 semantics.
    """
    client = _build_test_client(tmp_path)

    missing_patient = client.get("/fhir/Patient/pt-999")
    assert missing_patient.status_code == 404

    missing_resources = client.get("/fhir/Observation", params={"patient": "pt-999", "category": "laboratory"})
    assert missing_resources.status_code == 404
