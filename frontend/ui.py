"""Gradio UI layout for Clarke dashboard and core screen transitions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import gradio as gr

from frontend.components import build_patient_card, build_status_badge
from frontend.state import initial_consultation_state, select_patient, show_screen
from frontend.theme import clarke_theme

CLINIC_LIST_PATH = Path("data/clinic_list.json")
FHIR_BUNDLE_DIR = Path("data/fhir_bundles")


def load_clinic_list(path: Path = CLINIC_LIST_PATH) -> dict[str, Any]:
    """Load clinic list data for dashboard rendering.

    Args:
        path (Path): Path to clinic roster JSON file.

    Returns:
        dict[str, Any]: Clinic metadata and patient list payload.
    """

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _trend_symbol(trend: str) -> str:
    """Map trend labels to compact visual symbols.

    Args:
        trend (str): Trend label string such as rising, falling, or stable.

    Returns:
        str: Symbol corresponding to trend direction.
    """

    normalised = (trend or "").strip().lower()
    if normalised == "rising":
        return "↑"
    if normalised == "falling":
        return "↓"
    return "→"


def _format_patient_context_html(context: dict[str, Any]) -> str:
    """Render patient context sections as HTML for the S2 side panel.

    Args:
        context (dict[str, Any]): Structured patient context payload.

    Returns:
        str: HTML markup for patient context display.
    """

    demographics = context.get("demographics", {})
    medications = context.get("medications", [])
    allergies = context.get("allergies", [])
    labs = context.get("recent_labs", [])
    imaging = context.get("recent_imaging", [])
    flags = context.get("clinical_flags", [])

    medication_items = "".join(
        f"<li>{escape(str(item.get('name', 'Medication')))}"
        f" {escape(str(item.get('dose', '')))} {escape(str(item.get('frequency', '')))}</li>"
        for item in medications
    ) or "<li>None documented</li>"

    allergy_items = "".join(
        f"<li>⚠ {escape(str(item.get('substance', 'Unknown')))} — {escape(str(item.get('reaction', 'Reaction not recorded')))}</li>"
        for item in allergies
    ) or "<li>No known allergies</li>"

    lab_items = "".join(
        f"<li>{escape(str(item.get('name', 'Lab')))}: {escape(str(item.get('value', '')))} {escape(str(item.get('unit', '')))} {_trend_symbol(str(item.get('trend', '')))}</li>"
        for item in labs
    ) or "<li>No recent labs</li>"

    imaging_items = "".join(
        f"<li>{escape(str(item.get('type', 'Imaging')))} ({escape(str(item.get('date', '')))}): {escape(str(item.get('summary', '')))}</li>"
        for item in imaging
    ) or "<li>No recent imaging</li>"

    problem_items = "".join(f"<li>{escape(str(problem))}</li>" for problem in context.get("problem_list", [])) or "<li>No active problems</li>"
    flag_items = "".join(f"<li>{escape(str(flag))}</li>" for flag in flags) or "<li>No active clinical flags</li>"

    return f"""
    <div class=\"clarke-card\" style=\"padding:16px;\">
      <h4 style=\"margin-top:0;\">Demographics</h4>
      <p><strong>{escape(str(demographics.get('name', 'Unknown')))}</strong><br>
      DOB: {escape(str(demographics.get('dob', 'N/A')))}<br>
      NHS: <span class=\"mono\">{escape(str(demographics.get('nhs_number', 'N/A')))}</span><br>
      Sex: {escape(str(demographics.get('sex', 'N/A')))}</p>
      <h4>Problem List</h4><ul>{problem_items}</ul>
      <h4>Medications</h4><ul>{medication_items}</ul>
      <h4>Allergies</h4><ul>{allergy_items}</ul>
      <h4>Recent Labs</h4><ul>{lab_items}</ul>
      <h4>Recent Imaging</h4><ul>{imaging_items}</ul>
      <h4>Clinical Flags</h4><ul>{flag_items}</ul>
    </div>
    """


def _load_mock_patient_context(patient_id: str) -> dict[str, Any]:
    """Load patient context from local FHIR bundle as a lightweight UI mock.

    Args:
        patient_id (str): Patient identifier used to select local bundle fixtures.

    Returns:
        dict[str, Any]: Context payload with demographics, problems, meds, allergies, and labs.
    """

    bundle_path = FHIR_BUNDLE_DIR / f"{patient_id}.json"
    if not bundle_path.exists():
        return {
            "demographics": {"name": "Unknown", "dob": "", "nhs_number": "", "sex": ""},
            "problem_list": [],
            "medications": [],
            "allergies": [],
            "recent_labs": [],
            "recent_imaging": [],
            "clinical_flags": ["Context unavailable for selected patient."],
        }

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    demographics: dict[str, Any] = {"name": "", "dob": "", "nhs_number": "", "sex": ""}
    problems: list[str] = []
    medications: list[dict[str, str]] = []
    allergies: list[dict[str, str]] = []
    labs: list[dict[str, str]] = []
    imaging: list[dict[str, str]] = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        if resource_type == "Patient":
            name = resource.get("name", [{}])[0]
            full_name = " ".join([*(name.get("prefix", [])), *(name.get("given", [])), name.get("family", "")]).strip()
            nhs_number = ""
            for identifier in resource.get("identifier", []):
                if identifier.get("value"):
                    nhs_number = str(identifier.get("value"))
                    break
            demographics = {
                "name": full_name,
                "dob": str(resource.get("birthDate", "")),
                "nhs_number": nhs_number,
                "sex": str(resource.get("gender", "")).capitalize(),
            }
        elif resource_type == "Condition":
            problems.append(str(resource.get("code", {}).get("text", "")))
        elif resource_type == "MedicationRequest":
            medications.append(
                {
                    "name": str(resource.get("medicationCodeableConcept", {}).get("text", "Medication")),
                    "dose": "",
                    "frequency": "",
                }
            )
        elif resource_type == "AllergyIntolerance":
            allergies.append(
                {
                    "substance": str(resource.get("code", {}).get("text", "Allergy")),
                    "reaction": str(resource.get("reaction", [{}])[0].get("manifestation", [{}])[0].get("text", "Not recorded")),
                }
            )
        elif resource_type == "Observation" and "laboratory" in str(resource.get("category", [{}])[0].get("coding", [{}])[0].get("code", "")):
            labs.append(
                {
                    "name": str(resource.get("code", {}).get("text", "Lab")),
                    "value": str(resource.get("valueQuantity", {}).get("value", "")),
                    "unit": str(resource.get("valueQuantity", {}).get("unit", "")),
                    "trend": "stable",
                }
            )
        elif resource_type == "DiagnosticReport":
            imaging.append(
                {
                    "type": str(resource.get("code", {}).get("text", "Imaging")),
                    "date": str(resource.get("effectiveDateTime", ""))[:10],
                    "summary": str(resource.get("conclusion", "No conclusion provided.")),
                }
            )

    return {
        "demographics": demographics,
        "problem_list": [item for item in problems if item],
        "medications": medications,
        "allergies": allergies,
        "recent_labs": labs[:5],
        "recent_imaging": imaging[:3],
        "clinical_flags": ["Review latest bloods and medication adherence."],
    }


def _handle_patient_selection(state: dict[str, Any], patient_id: str) -> tuple[dict[str, Any], str, str, str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Update state and screen visibility when user selects a patient.

    Args:
        state (dict[str, Any]): Current UI session state.
        patient_id (str): Selected patient identifier.

    Returns:
        tuple[dict[str, Any], str, str, str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, context panel HTML, summary HTML, and visibility updates for S1-S6.
    """

    clinic_payload = load_clinic_list()
    patient = next((row for row in clinic_payload.get("patients", []) if row.get("id") == patient_id), None)
    if patient is None:
        return state, "Patient selection failed: patient not found.", "", "", *show_screen("s1")

    updated_state = select_patient(state, patient)
    updated_state["patient_context"] = _load_mock_patient_context(patient_id)
    context_html = _format_patient_context_html(updated_state["patient_context"])
    summary_html = f"<div class='clarke-card' style='padding:12px;'><p><strong>{escape(patient['name'])}</strong></p><p class='caption'>{escape(patient['summary'])}</p></div>"
    feedback = f"Loaded patient context for {patient['name']} ({patient['id']})."
    return updated_state, feedback, context_html, summary_html, *show_screen("s2")


def _handle_back_to_dashboard(state: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Navigate from context screen back to dashboard.

    Args:
        state (dict[str, Any]): Current application state.

    Returns:
        tuple[dict[str, Any], str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback text, and visibility updates for all screens.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s1"
    return updated_state, "Returned to dashboard.", *show_screen("s1")


def _handle_start_consultation(state: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Transition to live consultation and start recording timer.

    Args:
        state (dict[str, Any]): Current application state.

    Returns:
        tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback text, timer activation update, and visibility updates for all screens.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s3"
    updated_state["recording_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["consultation"]["status"] = "recording"
    return updated_state, "Consultation recording started.", gr.update(active=True), *show_screen("s3")


def _update_recording_timer(state: dict[str, Any]) -> str:
    """Compute MM:SS elapsed timer value for the active consultation recording.

    Args:
        state (dict[str, Any]): Current UI state containing recording start metadata.

    Returns:
        str: Elapsed consultation timer in MM:SS format.
    """

    started_at = str((state or {}).get("recording_started_at", "")).strip()
    if not started_at:
        return "00:00"
    elapsed_s = max(int((datetime.now(tz=timezone.utc) - datetime.fromisoformat(started_at)).total_seconds()), 0)
    minutes, seconds = divmod(elapsed_s, 60)
    return f"{minutes:02d}:{seconds:02d}"


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
            with gr.Row():
                with gr.Column(scale=5):
                    patient_context_panel = gr.HTML('<div class="skeleton-loader" style="height:220px;"></div>')
                with gr.Column(scale=7):
                    with gr.Column(elem_classes=["paper-container"]):
                        gr.Markdown("## Start Consultation")
                        gr.Markdown("Patient context is loaded. Start consultation recording when ready.")
                        start_consultation_button = gr.Button("Start Consultation", variant="primary")
                        back_to_dashboard_button = gr.Button("Back to Dashboard", variant="secondary")

        with gr.Column(visible=False) as screen_s3:
            with gr.Row():
                with gr.Column(scale=4):
                    patient_summary_panel = gr.HTML("<div class='clarke-card' style='padding:12px;'>No patient selected.</div>")
                with gr.Column(scale=8):
                    gr.HTML('<div class="recording-indicator active"></div>')
                    recording_timer = gr.Markdown("### 00:00")
                    recording_tick = gr.Timer(value=1.0, active=False)
                    consultation_audio = gr.Audio(sources=["microphone"], streaming=False, type="filepath", label="Consultation Audio")
                    end_consultation_button = gr.Button("End Consultation", variant="primary")
                    with gr.Accordion("Transcript", open=False):
                        gr.Markdown("Transcript will appear after consultation processing.")

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
                        outputs=[app_state, feedback_text, patient_context_panel, patient_summary_panel, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6],
                        show_progress="full",
                    )

        back_to_dashboard_button.click(
            _handle_back_to_dashboard,
            inputs=[app_state],
            outputs=[app_state, feedback_text, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6],
            show_progress="hidden",
        )

        start_consultation_button.click(
            _handle_start_consultation,
            inputs=[app_state],
            outputs=[app_state, feedback_text, recording_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6],
            show_progress="hidden",
        )

        recording_tick.tick(
            _update_recording_timer,
            inputs=[app_state],
            outputs=[recording_timer],
            show_progress="hidden",
        )

        end_consultation_button.click(
            lambda: "Consultation audio captured. Processing begins in Task 23.",
            outputs=[feedback_text],
        )

    return demo
