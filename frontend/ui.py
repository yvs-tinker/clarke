"""Gradio UI layout for Clarke dashboard and core screen transitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gradio as gr

from frontend.components import build_patient_card, build_status_badge
from frontend.state import initial_consultation_state, select_patient, show_screen
from frontend.theme import clarke_theme

CLINIC_LIST_PATH = Path("data/clinic_list.json")


def load_clinic_list(path: Path = CLINIC_LIST_PATH) -> dict[str, Any]:
    """Load clinic list data for dashboard rendering.

    Args:
        path (Path): Path to clinic roster JSON file.

    Returns:
        dict[str, Any]: Clinic metadata and patient list payload.
    """

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _handle_patient_selection(state: dict[str, Any], patient_id: str) -> tuple[dict[str, Any], str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Update state and screen visibility when user selects a patient.

    Args:
        state (dict[str, Any]): Current UI session state.
        patient_id (str): Selected patient identifier.

    Returns:
        tuple[dict[str, Any], str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback string, and visibility updates for S1-S6.
    """

    clinic_payload = load_clinic_list()
    patient = next((row for row in clinic_payload.get("patients", []) if row.get("id") == patient_id), None)
    if patient is None:
        return state, "Patient selection failed: patient not found.", *show_screen("s1")

    updated_state = select_patient(state, patient)
    feedback = f"Selected {patient['name']} ({patient['id']}). Transitioned to Patient Context (S2)."
    return updated_state, feedback, *show_screen("s2")


def build_ui() -> gr.Blocks:
    """Build the primary Clarke UI blocks for the dashboard flow.

    Args:
        None: Function reads local static assets and clinic JSON data.

    Returns:
        gr.Blocks: Configured Gradio Blocks application.
    """

    clinic_payload = load_clinic_list()
    clinician = clinic_payload.get("clinician", {})

    with gr.Blocks(theme=clarke_theme, css=Path("frontend/assets/style.css").read_text(encoding="utf-8"), title="Clarke") as demo:
        app_state = gr.State(initial_consultation_state())

        with gr.Row():
            gr.Image("frontend/assets/clarke_logo.svg", show_label=False, container=False, height=40, width=40)
            gr.HTML("<div><h3 style=\"margin:0;\">Clarke</h3><p class=\"caption\" style=\"margin:0;\">Clinical Documentation Copilot</p></div>")
            build_status_badge("ready")

        feedback_text = gr.Markdown("Select a patient card to open context.")

        with gr.Column(visible=False) as screen_s2:
            gr.Markdown("## S2 — Patient Context")
            gr.Markdown("Patient selected successfully. Full context panel is delivered in Task 22.")
        with gr.Column(visible=False) as screen_s3:
            gr.Markdown("## S3 — Live Consultation (Placeholder)")
        with gr.Column(visible=False) as screen_s4:
            gr.Markdown("## S4 — Processing (Placeholder)")
        with gr.Column(visible=False) as screen_s5:
            gr.Markdown("## S5 — Document Review (Placeholder)")
        with gr.Column(visible=False) as screen_s6:
            gr.Markdown("## S6 — Signed Off (Placeholder)")

        with gr.Column(visible=True) as screen_s1:
            with gr.Column(elem_classes=["hero-gradient"]):
                gr.Markdown(
                    f"### {clinician.get('name', 'Unknown Clinician')} — {clinician.get('specialty', 'Specialty')} — {clinic_payload.get('date', '')}"
                )
            for patient in clinic_payload.get("patients", []):
                with gr.Column(elem_classes=["clarke-card"]):
                    build_patient_card(patient)
                    patient_button = gr.Button("Open Patient", variant="primary")
                    patient_button.click(
                        _handle_patient_selection,
                        inputs=[app_state, gr.State(patient.get("id", ""))],
                        outputs=[app_state, feedback_text, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6],
                        show_progress="hidden",
                    )

    return demo
