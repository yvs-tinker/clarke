"""Tests for FHIR async client, tool wrappers, and deterministic query aggregation."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from backend.errors import FHIRClientError
from backend.fhir import mock_api
from backend.fhir.client import FHIRClient
from backend.fhir import tools, queries


@pytest.fixture
def asgi_client_patch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch httpx.AsyncClient to target mock FHIR FastAPI app via ASGI transport.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    Returns:
        None: Applies monkeypatch side effects for test duration.
    """

    transport = httpx.ASGITransport(app=mock_api.app)
    original_async_client = httpx.AsyncClient

    def build_client(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr("backend.fhir.client.httpx.AsyncClient", build_client)


def test_fhir_client_reads_core_endpoints(asgi_client_patch: None) -> None:
    """Verify FHIRClient returns JSON payloads for patient-scoped endpoint queries.

    Args:
        asgi_client_patch (None): Applied fixture to route requests to ASGI app.

    Returns:
        None: Assertions verify successful responses.
    """

    client = FHIRClient(fhir_server_url="http://testserver/fhir", timeout_s=5)

    patient = asyncio.run(client.get_patient("pt-001"))
    observations = asyncio.run(client.get_observations("pt-001"))

    assert patient["resourceType"] == "Patient"
    assert observations["resourceType"] == "Bundle"
    assert observations["total"] >= 1


def test_fhir_client_404_returns_empty_dict(asgi_client_patch: None) -> None:
    """Verify unknown patient requests return empty dictionaries for 404s.

    Args:
        asgi_client_patch (None): Applied fixture to route requests to ASGI app.

    Returns:
        None: Assertions verify 404-empty behaviour.
    """

    client = FHIRClient(fhir_server_url="http://testserver/fhir", timeout_s=5)
    missing = asyncio.run(client.get_patient("pt-999"))
    assert missing == {}


def test_fhir_client_retries_once_on_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify a single retry occurs after initial server-side error responses.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    Returns:
        None: Assertions validate retry semantics.
    """

    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(status_code=500, json={"detail": "temporary"})
        return httpx.Response(status_code=200, json={"resourceType": "Bundle", "entry": [], "total": 0})

    transport = httpx.MockTransport(handler)
    original_async_client = httpx.AsyncClient

    def build_client(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr("backend.fhir.client.httpx.AsyncClient", build_client)

    client = FHIRClient(fhir_server_url="http://retry/fhir", timeout_s=5)
    response = asyncio.run(client.get_conditions("pt-001"))

    assert response["resourceType"] == "Bundle"
    assert attempts["count"] == 2


def test_fhir_client_timeout_raises_contextual_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify timeout exceptions are raised with contextual FHIR endpoint details.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    Returns:
        None: Assertion verifies timeout failure semantics.
    """

    class TimeoutClient:
        """Minimal async context manager that always raises timeout on GET.

        Args:
            None: Created by monkeypatch in tests.

        Returns:
            None: Helper class for timeout simulation.
        """

        async def __aenter__(self) -> "TimeoutClient":
            """Enter async context manager.

            Args:
                None: No parameters.

            Returns:
                TimeoutClient: Context-managed instance.
            """

            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            """Exit async context manager.

            Args:
                exc_type (Any): Exception type when raised.
                exc (Any): Exception instance when raised.
                tb (Any): Traceback when raised.

            Returns:
                None: No exception suppression.
            """

            return None

        async def get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
            """Raise timeout for every request.

            Args:
                url (str): Requested URL string.
                params (dict[str, Any] | None): Request query parameters.

            Returns:
                httpx.Response: Never returns because timeout is raised.
            """

            raise httpx.TimeoutException("simulated timeout")

    monkeypatch.setattr("backend.fhir.client.httpx.AsyncClient", lambda *a, **k: TimeoutClient())

    client = FHIRClient(fhir_server_url="http://timeout/fhir", timeout_s=1)
    with pytest.raises(FHIRClientError, match="timeout"):
        asyncio.run(client.get_observations("pt-001"))


def test_tools_and_queries_aggregate_expected_lists(asgi_client_patch: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify tool wrappers and query aggregation return resource lists for pt-001.

    Args:
        asgi_client_patch (None): Applied fixture to route requests to ASGI app.
        monkeypatch (pytest.MonkeyPatch): Fixture for replacing default tool client.

    Returns:
        None: Assertions validate list extraction and aggregation keys.
    """

    patched_client = FHIRClient(fhir_server_url="http://testserver/fhir", timeout_s=5)
    monkeypatch.setattr(tools, "DEFAULT_FHIR_CLIENT", patched_client)

    patients = asyncio.run(tools.search_patients("Thompson"))
    conditions = asyncio.run(tools.get_conditions("pt-001"))
    context = asyncio.run(queries.get_full_patient_context("pt-001"))

    assert patients
    assert conditions
    assert context["medications"]
    assert context["observations"]
    assert context["allergies"]
    assert "encounters" in context
