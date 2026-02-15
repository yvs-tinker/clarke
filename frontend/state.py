"""Frontend state helpers for Clarke screen navigation."""

from __future__ import annotations

from typing import Any

import gradio as gr

SCREEN_ORDER: tuple[str, ...] = ("s1", "s2", "s3", "s4", "s5", "s6")


def initial_consultation_state() -> dict[str, Any]:
    """Build the initial consultation state payload.

    Args:
        None: This function has no input parameters.

    Returns:
        dict[str, Any]: Default consultation state structure for gr.State.
    """

    return {
        "screen": "s1",
        "consultation": {"id": None, "status": "idle"},
        "selected_patient": None,
        "patient_context": None,
        "generated_document": None,
        "signed_document_text": "",
        "captured_audio_path": "",
        "processing_started_at": None,
        "processing_step": 0,
        "processing_steps": [],
        "recording_started_at": None,
        "current_patient_index": 0,
        "completed_patients": [],
        "signed_letters": {},
    }


def show_screen(screen_name: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Generate Gradio visibility updates for all six screen containers.

    Args:
        screen_name (str): Screen identifier to display (s1-s6).

    Returns:
        tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
            Ordered Gradio `update` payloads matching SCREEN_ORDER.
    """

    if screen_name not in SCREEN_ORDER:
        screen_name = "s1"
    return tuple(gr.update(visible=name == screen_name) for name in SCREEN_ORDER)


def select_patient(state: dict[str, Any], patient: dict[str, Any]) -> dict[str, Any]:
    """Update UI state after selecting a patient card.

    Args:
        state (dict[str, Any]): Current application state object.
        patient (dict[str, Any]): Selected patient summary payload.

    Returns:
        dict[str, Any]: Updated state with selected patient and S2 screen target.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["selected_patient"] = patient
    updated_state["screen"] = "s2"
    return updated_state
