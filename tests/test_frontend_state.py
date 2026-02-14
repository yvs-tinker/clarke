"""Unit tests for frontend state helpers and reusable components."""

from datetime import datetime, timedelta, timezone

from frontend.components import build_patient_card, build_status_badge
from frontend.state import initial_consultation_state, show_screen
from frontend.ui import _format_patient_context_html, _trend_symbol, _update_recording_timer


def test_initial_consultation_state_defaults() -> None:
    """Ensure initial consultation state starts on dashboard.

    Args:
        None: Test has no runtime parameters.

    Returns:
        None: Assertions validate expected defaults.
    """

    state = initial_consultation_state()
    assert state["screen"] == "s1"
    assert state["selected_patient"] is None


def test_show_screen_marks_only_selected_visible() -> None:
    """Ensure visibility tuple marks exactly one active screen.

    Args:
        None: Test has no runtime parameters.

    Returns:
        None: Assertions validate screen visibility map.
    """

    visibility = show_screen("s3")
    assert len(visibility) == 6
    assert visibility[2]["visible"] is True
    assert sum(1 for item in visibility if item["visible"]) == 1


def test_component_builders_emit_html_values() -> None:
    """Ensure component builders return expected HTML payloads.

    Args:
        None: Test has no runtime parameters.

    Returns:
        None: Assertions validate rendered component values.
    """

    patient_card = build_patient_card(
        {
            "id": "pt-001",
            "name": "Mrs. Margaret Thompson",
            "age": 67,
            "sex": "Female",
            "time": "14:00",
            "summary": "Follow-up",
        }
    )
    badge = build_status_badge("ready")

    assert "Mrs. Margaret Thompson" in patient_card.value
    assert "status-amber" in badge.value


def test_patient_context_html_contains_required_sections() -> None:
    """Ensure context renderer outputs all S2 panel section headings.

    Args:
        None: Test has no runtime parameters.

    Returns:
        None: Assertions validate required section labels in generated HTML.
    """

    html = _format_patient_context_html(
        {
            "demographics": {"name": "Test Patient", "dob": "2000-01-01", "nhs_number": "123", "sex": "Female"},
            "problem_list": ["Condition"],
            "medications": [{"name": "Metformin", "dose": "1 g", "frequency": "BD"}],
            "allergies": [{"substance": "Penicillin", "reaction": "Rash"}],
            "recent_labs": [{"name": "HbA1c", "value": "55", "unit": "mmol/mol", "trend": "rising"}],
            "recent_imaging": [{"type": "CXR", "date": "2026-01-02", "summary": "Clear"}],
            "clinical_flags": ["Flag"],
        }
    )

    assert "Demographics" in html
    assert "Problem List" in html
    assert "Medications" in html
    assert "Allergies" in html
    assert "Recent Labs" in html
    assert "Recent Imaging" in html
    assert "Clinical Flags" in html
    assert "⚠" in html


def test_trend_symbol_and_timer_helpers() -> None:
    """Ensure trend symbols and elapsed timer formatting behave as expected.

    Args:
        None: Test has no runtime parameters.

    Returns:
        None: Assertions validate helper outputs.
    """

    assert _trend_symbol("rising") == "↑"
    assert _trend_symbol("falling") == "↓"
    assert _trend_symbol("stable") == "→"

    started_at = (datetime.now(tz=timezone.utc) - timedelta(seconds=65)).isoformat()
    timer = _update_recording_timer({"recording_started_at": started_at})
    assert timer in {"01:05", "01:04", "01:06"}
