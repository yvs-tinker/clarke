"""Unit tests for frontend state helpers and reusable components."""

from frontend.components import build_patient_card, build_status_badge
from frontend.state import initial_consultation_state, show_screen


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
