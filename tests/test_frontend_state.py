"""Unit tests for frontend state helpers and reusable components."""

from datetime import datetime, timedelta, timezone

from frontend.components import build_patient_card, build_status_badge
from frontend.state import initial_consultation_state, show_screen
from frontend.ui import (
    _build_generated_document,
    _build_processing_bar_html,
    _format_patient_context_html,
    _poll_processing_progress,
    _render_letter_sections,
    _sign_off_document,
    _trend_symbol,
    _update_recording_timer,
)


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
    assert "clarke-badge-review" in badge.value


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
    assert "clarke-clinical-flag" in html


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
    assert timer in {
        "<div class='clarke-recording-timer'>01:05</div>",
        "<div class='clarke-recording-timer'>01:04</div>",
        "<div class='clarke-recording-timer'>01:06</div>",
    }


def test_processing_helpers_and_document_lifecycle(tmp_path, monkeypatch) -> None:
    """Ensure processing progression and sign-off helpers produce expected outputs.

    Args:
        tmp_path: Pytest temporary path fixture for file isolation.
        monkeypatch: Pytest monkeypatch fixture for cwd redirection.

    Returns:
        None: Assertions validate helper and workflow outputs.
    """

    monkeypatch.chdir(tmp_path)
    (tmp_path / "data" / "demo").mkdir(parents=True)

    bar_html = _build_processing_bar_html(1)
    assert "clarke-progress-segment active" in bar_html

    sections = _render_letter_sections([{"heading": "A", "content": "B"}])
    assert len(sections) == 4
    assert sections[0].startswith("A")

    state = {
        "selected_patient": {"name": "Mrs. Margaret Thompson"},
        "patient_context": {
            "demographics": {"nhs_number": "1234567890"},
            "problem_list": ["Type 2 diabetes mellitus"],
            "recent_labs": [{"name": "HbA1c", "value": "55", "unit": "mmol/mol"}],
            "allergies": [{"substance": "Penicillin", "reaction": "Rash"}],
        },
        "consultation": {"status": "processing"},
        "processing_step": 2,
        "processing_steps": ["Finalising transcript…", "Synthesising patient context…", "Generating clinical letter…"],
        "processing_started_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    generated = _build_generated_document(state)
    assert generated["status"] == "ready_for_review"

    progressed = _poll_processing_progress(state)
    assert progressed[0]["screen"] == "s5"
    assert progressed[1].startswith("Processing complete")

    signed = _sign_off_document(progressed[0], "Section 1\nLine", "Section 2\nLine", "", "")
    assert "Signed Letter" in signed[2]
    assert (tmp_path / "data" / "demo" / "latest_signed_letter.txt").exists()
