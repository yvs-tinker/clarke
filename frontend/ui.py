"""Gradio UI layout for Clarke dashboard and end-to-end consultation flow."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import gradio as gr
import httpx

from frontend.components import build_patient_card, build_status_badge
from frontend.state import initial_consultation_state, select_patient, show_screen
from frontend.theme import clarke_theme

CLINIC_LIST_PATH = Path("data/clinic_list.json")
API_BASE_URL = os.getenv("CLARKE_API_BASE_URL", "http://127.0.0.1:7860/api/v1")


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


def _api_request(method: str, endpoint: str, **kwargs: Any) -> Any:
    """Execute an HTTP request to the Clarke backend API.

    Args:
        method (str): HTTP method name.
        endpoint (str): API path beginning with '/'.
        **kwargs (Any): Additional request keyword arguments.

    Returns:
        Any: Parsed JSON response payload.
    """

    timeout = kwargs.pop("timeout", 30.0)
    with httpx.Client(timeout=timeout) as client:
        response = client.request(method, f"{API_BASE_URL}{endpoint}", **kwargs)
    response.raise_for_status()
    return response.json()


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

    problem_items = "".join(f"<li>{escape(str(problem))}</li>" for problem in context.get("problem_list", [])) or "<li>No active problems</li>"
    medication_items = "".join(
        f"<li class='clarke-medication-item'>{escape(str(item.get('name', 'Medication')))}"
        f" <span class='clarke-medication-dose'>{escape(str(item.get('dose', '')))} {escape(str(item.get('frequency', '')))}</span></li>"
        for item in medications
    ) or "<li class='clarke-medication-item'>None documented</li>"
    allergy_items = "".join(
        f"<li class='clarke-allergy-item'>{escape(str(item.get('substance', 'Unknown')))} — {escape(str(item.get('reaction', 'Reaction not recorded')))}</li>"
        for item in allergies
    ) or "<li>No known allergies</li>"
    lab_items = "".join(
        f"<li><span class='clarke-lab-value'>{escape(str(item.get('name', 'Lab')))}: {escape(str(item.get('value', '')))} {escape(str(item.get('unit', '')))}</span>"
        f" <span class='clarke-trend-{str(item.get('trend', 'stable')).strip().lower().replace('rising', 'up').replace('falling', 'down')}'></span></li>"
        for item in labs
    ) or "<li>No recent labs</li>"
    imaging_items = "".join(
        f"<li>{escape(str(item.get('type', 'Imaging')))} ({escape(str(item.get('date', '')))}): {escape(str(item.get('summary', '')))}</li>"
        for item in imaging
    ) or "<li>No recent imaging</li>"
    flag_items = "".join(f"<li class='clarke-clinical-flag'>{escape(str(flag))}</li>" for flag in flags) or "<li>No active clinical flags</li>"

    return f"""
    <div class="clarke-card">
      <div class="clarke-context-section">
        <h3>Demographics</h3>
        <p><strong>{escape(str(demographics.get('name', 'Unknown')))}</strong><br>
        DOB: {escape(str(demographics.get('dob', 'N/A')))}<br>
        NHS: <span class="mono">{escape(str(demographics.get('nhs_number', 'N/A')))}</span><br>
        Sex: {escape(str(demographics.get('sex', 'N/A')))}</p>
      </div>
      <div class="clarke-context-section"><h3>Problem List</h3><ul>{problem_items}</ul></div>
      <div class="clarke-context-section"><h3>Medications</h3><ul>{medication_items}</ul></div>
      <div class="clarke-context-section"><h3>Allergies</h3><ul>{allergy_items}</ul></div>
      <div class="clarke-context-section"><h3>Recent Labs</h3><ul>{lab_items}</ul></div>
      <div class="clarke-context-section"><h3>Recent Imaging</h3><ul>{imaging_items}</ul></div>
      <div class="clarke-context-section"><h3>Clinical Flags</h3><ul>{flag_items}</ul></div>
    </div>
    """


def _build_processing_bar_html(active_index: int) -> str:
    """Render a three-step segmented processing progress bar.

    Args:
        active_index (int): Zero-based index of current active processing stage.

    Returns:
        str: HTML snippet for processing progress bar.
    """

    segments = []
    for index in range(3):
        state_class = 'clarke-progress-segment complete' if index < active_index else 'clarke-progress-segment active' if index == active_index else 'clarke-progress-segment'
        segments.append(f"<div class='{state_class}'></div>")
    return f"<div class='clarke-progress-bar'>{''.join(segments)}</div>"


def _render_letter_sections(letter_sections: list[dict[str, str]]) -> tuple[str, str, str, str]:
    """Map generated letter sections onto fixed textbox outputs.

    Args:
        letter_sections (list[dict[str, str]]): Ordered letter sections with heading/content keys.

    Returns:
        tuple[str, str, str, str]: Four section strings for review textboxes.
    """

    resolved_sections = list(letter_sections)
    while len(resolved_sections) < 4:
        resolved_sections.append({"heading": f"Section {len(resolved_sections) + 1}", "content": ""})
    return tuple(f"{s.get('heading', '')}\n{s.get('content', '').strip()}".strip() for s in resolved_sections[:4])


def _build_generated_document(state: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic fallback letter when backend document is unavailable.

    Args:
        state (dict[str, Any]): Current session state containing patient and context metadata.

    Returns:
        dict[str, Any]: Document payload with editable sections and FHIR-derived highlights.
    """

    selected_patient = (state or {}).get("selected_patient") or {}
    patient_context = (state or {}).get("patient_context") or {}
    first_lab = (patient_context.get("recent_labs") or [{"name": "Lab", "value": "", "unit": ""}])[0]
    first_problem = (patient_context.get("problem_list") or ["Clinical issue"])[0]
    sections = [
        {"heading": "Clinical Summary", "content": f"Consultation focused on {first_problem.lower()}."},
        {"heading": "Assessment", "content": f"Latest result: {first_lab.get('name')} {first_lab.get('value')} {first_lab.get('unit')}"},
        {"heading": "Safety and Risks", "content": "Reviewed medication and allergy safety."},
        {"heading": "Plan", "content": "Continue treatment and schedule follow-up."},
    ]
    return {"title": "NHS Clinic Letter", "status": "ready_for_review", "sections": sections, "patient_name": selected_patient.get("name", "Patient")}


def _update_recording_timer(state: dict[str, Any]) -> str:
    """Compute MM:SS elapsed timer value for the active consultation recording.

    Args:
        state (dict[str, Any]): Current UI state containing recording start metadata.

    Returns:
        str: Elapsed consultation timer in MM:SS format.
    """

    started_at = str((state or {}).get("recording_started_at", "")).strip()
    if not started_at:
        return "<div class='clarke-recording-timer'>00:00</div>"
    elapsed_s = max(int((datetime.now(tz=timezone.utc) - datetime.fromisoformat(started_at)).total_seconds()), 0)
    minutes, seconds = divmod(elapsed_s, 60)
    return f"<div class='clarke-recording-timer'>{minutes:02d}:{seconds:02d}</div>"


def _handle_patient_selection(state: dict[str, Any], patient_id: str) -> tuple[dict[str, Any], str, str, str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Update state and call backend context endpoint when user selects a patient.

    Args:
        state (dict[str, Any]): Current UI session state.
        patient_id (str): Selected patient identifier.

    Returns:
        tuple[dict[str, Any], str, str, str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, context HTML, summary HTML, and visibility updates.
    """

    clinic_payload = load_clinic_list()
    patient = next((row for row in clinic_payload.get("patients", []) if row.get("id") == patient_id), None)
    if patient is None:
        return state, "Patient selection failed: patient not found.", "", "", *show_screen("s1")

    updated_state = select_patient(state, patient)
    try:
        context = _api_request("POST", f"/patients/{patient_id}/context")
    except Exception as exc:
        context = updated_state.get("patient_context") or {}
        feedback = f"Patient selected but context call failed: {exc}"
    else:
        feedback = f"Loaded patient context for {patient['name']} ({patient['id']})."

    updated_state["patient_context"] = context
    context_html = _format_patient_context_html(context)
    summary_html = f"<div class='clarke-card'><p><strong>{escape(patient['name'])}</strong></p><p class='caption'>{escape(patient['summary'])}</p></div>"
    return updated_state, feedback, context_html, summary_html, *show_screen("s2")


def _handle_back_to_dashboard(state: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Navigate from context screen back to dashboard.

    Args:
        state (dict[str, Any]): Current application state.

    Returns:
        tuple[dict[str, Any], str, dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback text, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s1"
    return updated_state, "Returned to dashboard.", *show_screen("s1")


def _handle_start_consultation(state: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Start consultation by calling backend and storing consultation_id.

    Args:
        state (dict[str, Any]): Current application state.

    Returns:
        tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, timer update, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    patient_id = str((updated_state.get("selected_patient") or {}).get("id", ""))
    if not patient_id:
        return updated_state, "Please select a patient first.", gr.update(active=False), *show_screen("s1")

    try:
        payload = _api_request("POST", "/consultations/start", json={"patient_id": patient_id})
    except Exception as exc:
        return updated_state, f"Failed to start consultation: {exc}", gr.update(active=False), *show_screen("s2")

    updated_state["consultation"] = {"id": payload.get("consultation_id"), "status": payload.get("status", "recording")}
    updated_state["recording_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["screen"] = "s3"
    return updated_state, "Consultation recording started.", gr.update(active=True), *show_screen("s3")


def _stage_from_pipeline(stage: str) -> tuple[str, int]:
    """Map backend pipeline stage to UI label and progress segment index.

    Args:
        stage (str): Backend pipeline stage value.

    Returns:
        tuple[str, int]: Display label and active segment index.
    """

    mapping = {
        "transcribing": ("<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", 0),
        "retrieving_context": ("<div class='clarke-stage-label active clarke-stage-active'>Synthesising patient context…</div>", 1),
        "generating_document": ("<div class='clarke-stage-label active clarke-stage-active'>Generating clinical letter…</div>", 2),
        "complete": ("<div class='clarke-stage-label active clarke-stage-active'>Generating clinical letter…</div>", 2),
    }
    return mapping.get(stage, ("<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", 0))


def _start_processing(state: dict[str, Any], audio_path: str | None) -> tuple[dict[str, Any], str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Upload audio and end consultation, then transition to processing screen.

    Args:
        state (dict[str, Any]): Current UI state.
        audio_path (str | None): File path returned by Gradio audio component.

    Returns:
        tuple[dict[str, Any], str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, stage label, progress bar, timer label, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    consultation_id = str((updated_state.get("consultation") or {}).get("id", ""))
    if not consultation_id:
        return updated_state, "Consultation session is missing. Start consultation again.", "<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", _build_processing_bar_html(0), "<div class='clarke-processing-timer'>Elapsed: 00:00</div>", gr.update(active=False), *show_screen("s3")
    if not audio_path:
        return updated_state, "Please capture audio before ending consultation.", "<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", _build_processing_bar_html(0), "<div class='clarke-processing-timer'>Elapsed: 00:00</div>", gr.update(active=False), *show_screen("s3")

    try:
        with Path(audio_path).open("rb") as stream:
            _api_request(
                "POST",
                f"/consultations/{consultation_id}/audio",
                files={"audio_file": (Path(audio_path).name, stream, "audio/wav")},
                data={"is_final": "true"},
                timeout=120.0,
            )
        _api_request("POST", f"/consultations/{consultation_id}/end", timeout=180.0)
    except Exception as exc:
        return updated_state, f"Failed to end consultation: {exc}", "<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", _build_processing_bar_html(0), "<div class='clarke-processing-timer'>Elapsed: 00:00</div>", gr.update(active=False), *show_screen("s3")

    updated_state["captured_audio_path"] = audio_path
    updated_state["processing_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["consultation"]["status"] = "processing"
    updated_state["screen"] = "s4"
    return updated_state, "Consultation ended. Processing audio and generating document.", "<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", _build_processing_bar_html(0), "<div class='clarke-processing-timer'>Elapsed: 00:00</div>", gr.update(active=True), *show_screen("s4")


def _poll_processing_progress(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str, dict[str, Any], str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Poll backend consultation progress and transition to review when complete.

    Args:
        state (dict[str, Any]): Current state containing consultation metadata.

    Returns:
        tuple[dict[str, Any], str, str, str, dict[str, Any], str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state and UI updates for processing/review screens.
    """

    updated_state = dict(state or initial_consultation_state())
    consultation_id = str((updated_state.get("consultation") or {}).get("id", ""))

    started_at = str(updated_state.get("processing_started_at", "") or "")
    elapsed_label = "<div class='clarke-processing-timer'>Elapsed: 00:00</div>"
    if started_at:
        elapsed_s = max(int((datetime.now(tz=timezone.utc) - datetime.fromisoformat(started_at)).total_seconds()), 0)
        minutes, seconds = divmod(elapsed_s, 60)
        elapsed_label = f"<div class='clarke-processing-timer'>Elapsed: {minutes:02d}:{seconds:02d}</div>"

    if not consultation_id:
        generated_document = _build_generated_document(updated_state)
        updated_state["generated_document"] = generated_document
        updated_state["consultation"] = updated_state.get("consultation") or {"id": None, "status": "review"}
        updated_state["consultation"]["status"] = "review"
        updated_state["screen"] = "s5"
        section_1, section_2, section_3, section_4 = _render_letter_sections(generated_document.get("sections", []))
        return updated_state, "Processing complete. Review the generated clinic letter.", "<div class='clarke-stage-label active clarke-stage-active'>Generating clinical letter…</div>", _build_processing_bar_html(2), gr.update(active=False), elapsed_label, section_1, section_2, section_3, section_4, gr.update(), gr.update(), gr.update(value="Ready for Review", variant="secondary"), *show_screen("s5")

    try:
        progress = _api_request("GET", f"/consultations/{consultation_id}/progress")
    except Exception as exc:
        return updated_state, f"Progress polling failed: {exc}", "<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", _build_processing_bar_html(0), gr.update(active=False), elapsed_label, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), *show_screen("s4")

    stage = str(progress.get("stage", "transcribing"))
    stage_label, segment_index = _stage_from_pipeline(stage)

    if stage != "complete":
        return updated_state, f"Processing in progress: {stage_label}", stage_label, _build_processing_bar_html(segment_index), gr.update(active=True), elapsed_label, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), *show_screen("s4")

    document_payload = _api_request("GET", f"/consultations/{consultation_id}/document").get("document")
    if document_payload is None:
        document_payload = _build_generated_document(updated_state)

    sections = [{"heading": s.get("heading", "Section"), "content": s.get("content", "")} for s in document_payload.get("sections", [])]
    updated_state["generated_document"] = document_payload
    updated_state["consultation"]["status"] = "review"
    updated_state["screen"] = "s5"

    section_1, section_2, section_3, section_4 = _render_letter_sections(sections)
    highlights = [
        f"NHS Number: {document_payload.get('nhs_number', 'N/A')}",
        f"Patient: {document_payload.get('patient_name', 'N/A')}",
        f"Status: {document_payload.get('status', 'review')}",
    ]
    highlight_markup = "<br>".join(f"<span class='mono'>{escape(item)}</span>" for item in highlights)

    return (
        updated_state,
        "Processing complete. Review the generated clinic letter.",
        stage_label,
        _build_processing_bar_html(2),
        gr.update(active=False),
        elapsed_label,
        section_1,
        section_2,
        section_3,
        section_4,
        f"<div class='clarke-card'>{highlight_markup}</div>",
        "",
        gr.update(value="Ready for Review", variant="secondary"),
        *show_screen("s5"),
    )


def _regenerate_document(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Restart processing view before polling backend completion status again.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state and screen visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["processing_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["consultation"]["status"] = "processing"
    updated_state["screen"] = "s4"
    return updated_state, "Regenerating entire clinic letter.", "<div class='clarke-stage-label active clarke-stage-active'>Finalising transcript…</div>", _build_processing_bar_html(0), "<div class='clarke-processing-timer'>Elapsed: 00:00</div>", gr.update(value="Ready for Review", variant="secondary"), gr.update(active=True), *show_screen("s4")


def _cancel_processing(state: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Cancel processing workflow and return to live consultation screen.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s3"
    updated_state["consultation"]["status"] = "recording"
    return updated_state, "Processing cancelled. Returned to consultation.", gr.update(active=False), *show_screen("s3")


def _sign_off_document(state: dict[str, Any], section_1: str, section_2: str, section_3: str, section_4: str) -> tuple[dict[str, Any], str, str, dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Persist edited sections to backend sign-off endpoint and show final letter.

    Args:
        state (dict[str, Any]): Current UI state.
        section_1 (str): Edited section one text.
        section_2 (str): Edited section two text.
        section_3 (str): Edited section three text.
        section_4 (str): Edited section four text.

    Returns:
        tuple[dict[str, Any], str, str, dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state and signed-off UI content.
    """

    updated_state = dict(state or initial_consultation_state())
    consultation_id = str((updated_state.get("consultation") or {}).get("id", ""))
    edited_sections = [section_1, section_2, section_3, section_4]

    payload_sections: list[dict[str, str]] = []
    for index, section_text in enumerate(edited_sections):
        if not section_text.strip():
            continue
        lines = section_text.splitlines()
        heading = lines[0].strip() if lines else f"Section {index + 1}"
        content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        payload_sections.append({"heading": heading, "content": content})

    if consultation_id:
        try:
            _api_request("POST", f"/consultations/{consultation_id}/document/sign-off", json={"sections": payload_sections})
        except Exception as exc:
            return updated_state, f"Sign-off failed: {exc}", "", gr.update(value="Ready for Review", variant="secondary"), "", gr.update(), *show_screen("s5")

    signed_letter = "\n\n".join(part.strip() for part in edited_sections if part and part.strip())
    updated_state["signed_document_text"] = signed_letter
    updated_state["consultation"]["status"] = "signed_off"
    updated_state["screen"] = "s6"

    export_path = Path("data") / "demo" / "latest_signed_letter.txt"
    export_path.write_text(signed_letter + "\n", encoding="utf-8")

    return updated_state, "Document signed off. You can now copy or download the letter.", f"### Signed Letter\n\n{signed_letter}", gr.update(value="Signed Off ✓", variant="primary"), signed_letter, gr.update(value=str(export_path)), *show_screen("s6")


def _next_patient(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str, str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Reset consultation workflow and return to dashboard after sign-off.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, str, str, str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Reset state and cleared UI content updates.
    """

    refreshed_state = initial_consultation_state()
    return refreshed_state, "Ready for next patient. Please select a patient card.", "", "", "", "", "", "", "", "", gr.update(value="Ready for Review", variant="secondary"), *show_screen("s1")


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

        with gr.Row(elem_classes=["clarke-header"]):
            gr.Image("frontend/assets/clarke_logo.svg", show_label=False, container=False, height=40, width=40, elem_classes=["clarke-logo-ring"])
            gr.HTML("<div><h3 style=\"margin:0;\">Clarke</h3><p class=\"caption\" style=\"margin:0;\">Clinical Documentation Copilot</p></div>")
            build_status_badge("ready")

        feedback_text = gr.Markdown("Select a patient card to open context.")

        with gr.Column(visible=False, elem_classes=["clarke-screen-enter"]) as screen_s2:
            with gr.Row():
                with gr.Column(scale=5):
                    patient_context_panel = gr.HTML('<div class="clarke-skeleton" style="height:220px;"></div>')
                with gr.Column(scale=7):
                    with gr.Column(elem_classes=["paper-container"]):
                        gr.Markdown("## Start Consultation")
                        gr.Markdown("Patient context is loaded. Start consultation recording when ready.")
                        start_consultation_button = gr.Button("Start Consultation", variant="primary", elem_classes=["clarke-btn-primary"])
                        back_to_dashboard_button = gr.Button("Back to Dashboard", variant="secondary", elem_classes=["clarke-btn-secondary"])

        with gr.Column(visible=False, elem_classes=["clarke-screen-enter"]) as screen_s3:
            with gr.Row():
                with gr.Column(scale=4):
                    patient_summary_panel = gr.HTML("<div class='clarke-card'>No patient selected.</div>")
                with gr.Column(scale=8):
                    gr.HTML('<div class="clarke-recording-indicator"><div class="clarke-recording-ring"></div><div class="clarke-recording-dot"></div><div class="clarke-recording-label">Recording…</div></div>')
                    recording_timer = gr.Markdown("<div class=\"clarke-recording-timer\">00:00</div>")
                    recording_tick = gr.Timer(value=1.0, active=False)
                    consultation_audio = gr.Audio(sources=["microphone", "upload"], streaming=False, type="filepath", label="Consultation Audio", elem_classes=["clarke-audio-container"])
                    end_consultation_button = gr.Button("End Consultation", variant="primary", elem_classes=["clarke-btn-primary"])

        with gr.Column(visible=False, elem_classes=["clarke-screen-enter"]) as screen_s4:
            with gr.Column(elem_classes=["paper-container"]):
                gr.Markdown("## Processing")
                processing_stage = gr.Markdown("<div class=\"clarke-stage-label active clarke-stage-active\">Finalising transcript…</div>")
                processing_progress_bar = gr.HTML(_build_processing_bar_html(0))
                processing_elapsed_timer = gr.Markdown("<div class=\"clarke-processing-timer\">Elapsed: 00:00</div>")
                processing_tick = gr.Timer(value=1.0, active=False)
                cancel_processing_button = gr.Button("Cancel", variant="stop", elem_classes=["clarke-btn-destructive"])

        with gr.Column(visible=False, elem_classes=["clarke-screen-enter"]) as screen_s5:
            with gr.Row():
                with gr.Column(scale=4):
                    gr.HTML("<div class='clarke-card' style='padding:12px;'><p><strong>Patient</strong></p></div>")
                with gr.Column(scale=8):
                    review_status_badge = gr.Label(value="Ready for Review", label="Status", elem_classes=["clarke-badge", "clarke-badge-review"])
                    review_fhir_values = gr.HTML("<div class='clarke-card'><span class='clarke-fhir-value'>FHIR values appear here.</span></div>")
                    with gr.Column(elem_classes=["paper-container", "clarke-document-reveal"]):
                        section_one_text = gr.Textbox(label="Section 1", lines=5, interactive=True, elem_classes=["clarke-section-editing"])
                        section_two_text = gr.Textbox(label="Section 2", lines=5, interactive=True, elem_classes=["clarke-section-editing"])
                        section_three_text = gr.Textbox(label="Section 3", lines=5, interactive=True, elem_classes=["clarke-section-editing"])
                        section_four_text = gr.Textbox(label="Section 4", lines=5, interactive=True, elem_classes=["clarke-section-editing"])
                    with gr.Row():
                        sign_off_button = gr.Button("Sign Off & Export", variant="primary", elem_classes=["clarke-btn-primary"])
                        regenerate_button = gr.Button("Regenerate Entire Letter", variant="secondary", elem_classes=["clarke-btn-secondary"])

        with gr.Column(visible=False, elem_classes=["clarke-screen-enter"]) as screen_s6:
            with gr.Column(elem_classes=["paper-container"]):
                signed_status_badge = gr.Label(value="Signed Off ✓", label="Status", elem_classes=["clarke-badge", "clarke-badge-signed"])
                signed_letter_markdown = gr.Markdown("### Signed letter will appear here.")
                copy_to_clipboard_text = gr.Textbox(label="Copy to Clipboard", interactive=False)
                download_text_file = gr.File(label="Download as Text")
                next_patient_button = gr.Button("Next Patient", variant="primary", elem_classes=["clarke-btn-gold"])

        with gr.Column(visible=True, elem_classes=["clarke-screen-enter"]) as screen_s1:
            with gr.Column(elem_classes=["clarke-hero-bg"]):
                gr.HTML(f"<div class='clarke-clinic-header'>{clinician.get('name', 'Unknown Clinician')} — {clinician.get('specialty', 'Specialty')} — {clinic_payload.get('date', '')}</div>")
            for patient in clinic_payload.get("patients", []):
                with gr.Column(elem_classes=["clarke-card"]):
                    build_patient_card(patient)
                    patient_button = gr.Button("Open Patient", variant="primary", elem_classes=["clarke-btn-gold"])
                    patient_button.click(_handle_patient_selection, inputs=[app_state, gr.State(patient.get("id", ""))], outputs=[app_state, feedback_text, patient_context_panel, patient_summary_panel, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="full")

        back_to_dashboard_button.click(_handle_back_to_dashboard, inputs=[app_state], outputs=[app_state, feedback_text, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        start_consultation_button.click(_handle_start_consultation, inputs=[app_state], outputs=[app_state, feedback_text, recording_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        recording_tick.tick(_update_recording_timer, inputs=[app_state], outputs=[recording_timer], show_progress="hidden")
        end_consultation_button.click(_start_processing, inputs=[app_state, consultation_audio], outputs=[app_state, feedback_text, processing_stage, processing_progress_bar, processing_elapsed_timer, processing_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="full")
        processing_tick.tick(_poll_processing_progress, inputs=[app_state], outputs=[app_state, feedback_text, processing_stage, processing_progress_bar, processing_tick, processing_elapsed_timer, section_one_text, section_two_text, section_three_text, section_four_text, review_fhir_values, copy_to_clipboard_text, review_status_badge, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        cancel_processing_button.click(_cancel_processing, inputs=[app_state], outputs=[app_state, feedback_text, processing_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        regenerate_button.click(_regenerate_document, inputs=[app_state], outputs=[app_state, feedback_text, processing_stage, processing_progress_bar, processing_elapsed_timer, review_status_badge, processing_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="full")
        sign_off_button.click(_sign_off_document, inputs=[app_state, section_one_text, section_two_text, section_three_text, section_four_text], outputs=[app_state, feedback_text, signed_letter_markdown, signed_status_badge, copy_to_clipboard_text, download_text_file, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="full")
        next_patient_button.click(_next_patient, inputs=[app_state], outputs=[app_state, feedback_text, section_one_text, section_two_text, section_three_text, section_four_text, signed_letter_markdown, copy_to_clipboard_text, processing_stage, processing_elapsed_timer, review_status_badge, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")

    return demo
