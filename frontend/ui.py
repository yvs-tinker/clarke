"""Gradio UI layout for Clarke dashboard and end-to-end consultation flow."""

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


def _start_processing(state: dict[str, Any], audio_path: str | None) -> tuple[dict[str, Any], str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Transition from recording to processing and initialise stage metadata.

    Args:
        state (dict[str, Any]): Current UI state before processing begins.
        audio_path (str | None): File path returned by Gradio audio component.

    Returns:
        tuple[dict[str, Any], str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, active stage, progress bar HTML, elapsed timer label,
            polling timer update, and visibility updates for S1-S6.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s4"
    updated_state["consultation"]["status"] = "processing"
    updated_state["processing_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["processing_step"] = 0
    updated_state["processing_steps"] = [
        "Finalising transcript…",
        "Synthesising patient context…",
        "Generating clinical letter…",
    ]
    updated_state["captured_audio_path"] = audio_path or ""
    return (
        updated_state,
        "Consultation ended. Processing audio and generating document.",
        "Finalising transcript…",
        _build_processing_bar_html(0),
        "00:00",
        gr.update(active=True),
        *show_screen("s4"),
    )


def _build_processing_bar_html(active_index: int) -> str:
    """Render a three-step segmented processing progress bar.

    Args:
        active_index (int): Zero-based index of current active processing stage.

    Returns:
        str: HTML snippet for processing progress bar.
    """

    segments: list[str] = []
    for index in range(3):
        segment_class = "processing-segment active" if index <= active_index else "processing-segment"
        segments.append(f"<div class='{segment_class}'></div>")
    return f"<div class='processing-bar'>{''.join(segments)}</div>"


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

    return tuple(
        f"{section.get('heading', f'Section {idx + 1}')}\n{section.get('content', '').strip()}".strip()
        for idx, section in enumerate(resolved_sections[:4])
    )


def _build_generated_document(state: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic mock generated letter from selected patient context.

    Args:
        state (dict[str, Any]): Current session state containing patient and context metadata.

    Returns:
        dict[str, Any]: Document payload with editable sections and FHIR-derived highlights.
    """

    selected_patient = (state or {}).get("selected_patient") or {}
    patient_context = (state or {}).get("patient_context") or {}
    demographics = patient_context.get("demographics", {})
    first_lab = (patient_context.get("recent_labs") or [{"name": "HbA1c", "value": "", "unit": ""}])[0]
    first_allergy = (patient_context.get("allergies") or [{"substance": "No known allergies", "reaction": ""}])[0]
    first_problem = (patient_context.get("problem_list") or ["Clinical problem not recorded"])[0]

    letter_sections = [
        {
            "heading": "Clinical Summary",
            "content": (
                f"Thank you for reviewing {selected_patient.get('name', 'this patient')} today. "
                f"This consultation focused on {first_problem.lower()}."
            ),
        },
        {
            "heading": "Assessment",
            "content": (
                f"Recent observations show {first_lab.get('name', 'laboratory result')} "
                f"{first_lab.get('value', '')} {first_lab.get('unit', '')}. "
                "The patient reported ongoing symptoms requiring follow-up."
            ),
        },
        {
            "heading": "Safety and Risks",
            "content": (
                f"Documented allergy: {first_allergy.get('substance', 'none recorded')} "
                f"({first_allergy.get('reaction', 'reaction not specified')})."
            ),
        },
        {
            "heading": "Plan",
            "content": "Continue current treatment, reinforce adherence, and repeat blood tests in 3 months.",
        },
    ]

    return {
        "title": "NHS Clinic Letter",
        "status": "ready_for_review",
        "sections": letter_sections,
        "fhir_highlights": [
            f"NHS Number: {demographics.get('nhs_number', 'N/A')}",
            f"Primary Problem: {first_problem}",
            f"Latest Lab: {first_lab.get('name', 'Lab')} {first_lab.get('value', '')} {first_lab.get('unit', '')}",
            f"Allergy: {first_allergy.get('substance', 'None recorded')}",
        ],
    }


def _poll_processing_progress(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str, dict[str, Any], str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Advance the processing stage and transition to review once complete.

    Args:
        state (dict[str, Any]): Current state containing processing metadata.

    Returns:
        tuple[dict[str, Any], str, str, str, dict[str, Any], str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, active stage label, progress bar HTML, polling timer update,
            elapsed timer label, four review section textbox values, FHIR highlights HTML,
            status badge update, export text value, download file update, and screen visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    steps = updated_state.get("processing_steps") or [
        "Finalising transcript…",
        "Synthesising patient context…",
        "Generating clinical letter…",
    ]
    current_step = int(updated_state.get("processing_step", 0))
    started_at = str(updated_state.get("processing_started_at", "")).strip()
    elapsed_label = "00:00"
    if started_at:
        elapsed_s = max(int((datetime.now(tz=timezone.utc) - datetime.fromisoformat(started_at)).total_seconds()), 0)
        minutes, seconds = divmod(elapsed_s, 60)
        elapsed_label = f"{minutes:02d}:{seconds:02d}"

    if current_step < len(steps) - 1:
        updated_state["processing_step"] = current_step + 1
        next_step = steps[current_step + 1]
        return (
            updated_state,
            f"Processing in progress: {next_step}",
            next_step,
            _build_processing_bar_html(current_step + 1),
            gr.update(active=True),
            elapsed_label,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            *show_screen("s4"),
        )

    generated_document = _build_generated_document(updated_state)
    updated_state["generated_document"] = generated_document
    updated_state["consultation"]["status"] = "review"
    updated_state["screen"] = "s5"

    section_1, section_2, section_3, section_4 = _render_letter_sections(generated_document.get("sections", []))
    highlight_markup = "<br>".join(f"<span class='mono'>{escape(item)}</span>" for item in generated_document.get("fhir_highlights", []))
    return (
        updated_state,
        "Processing complete. Review the generated clinic letter.",
        "Generating clinical letter…",
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
    """Restart processing from S5 and regenerate the full document.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback text, stage label, progress bar HTML, elapsed timer,
            status badge update, processing timer activation, and screen visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["processing_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["processing_step"] = 0
    updated_state["consultation"]["status"] = "processing"
    updated_state["screen"] = "s4"
    return (
        updated_state,
        "Regenerating entire clinic letter.",
        "Finalising transcript…",
        _build_processing_bar_html(0),
        "00:00",
        gr.update(value="Ready for Review", variant="secondary"),
        gr.update(active=True),
        *show_screen("s4"),
    )


def _cancel_processing(state: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Cancel processing workflow and return to live consultation screen.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback text, processing timer update, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s3"
    updated_state["consultation"]["status"] = "recording"
    return updated_state, "Processing cancelled. Returned to consultation.", gr.update(active=False), *show_screen("s3")


def _sign_off_document(state: dict[str, Any], section_1: str, section_2: str, section_3: str, section_4: str) -> tuple[dict[str, Any], str, str, dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Persist edited section text and transition to signed-off display.

    Args:
        state (dict[str, Any]): Current UI state with generated document.
        section_1 (str): Edited section one text.
        section_2 (str): Edited section two text.
        section_3 (str): Edited section three text.
        section_4 (str): Edited section four text.

    Returns:
        tuple[dict[str, Any], str, str, dict[str, Any], str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Updated state, feedback, read-only signed letter markdown, badge update,
            clipboard text, download file update, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    edited_sections = [section_1, section_2, section_3, section_4]
    signed_letter = "\n\n".join(part.strip() for part in edited_sections if part and part.strip())
    updated_state["signed_document_text"] = signed_letter
    updated_state["consultation"]["status"] = "signed_off"
    updated_state["screen"] = "s6"

    export_path = Path("data") / "demo" / "latest_signed_letter.txt"
    export_path.write_text(signed_letter + "\n", encoding="utf-8")

    return (
        updated_state,
        "Document signed off. You can now copy or download the letter.",
        f"### Signed Letter\n\n{signed_letter}",
        gr.update(value="Signed Off ✓", variant="primary"),
        signed_letter,
        gr.update(value=str(export_path)),
        *show_screen("s6"),
    )


def _next_patient(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str, str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
    """Reset consultation workflow and return to dashboard after sign-off.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, str, str, str, str, str, str, str, str, dict[str, Any], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool], dict[str, bool]]:
            Reset state, feedback text, cleared review/signed content, status badge update,
            and visibility updates for all screens.
    """

    refreshed_state = initial_consultation_state()
    refreshed_state["highlight_next_patient"] = True
    return (
        refreshed_state,
        "Ready for next patient. Please select a patient card.",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        gr.update(value="Ready for Review", variant="secondary"),
        *show_screen("s1"),
    )


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
            with gr.Column(elem_classes=["paper-container"]):
                gr.Markdown("## Processing")
                processing_stage = gr.Markdown("Finalising transcript…")
                processing_progress_bar = gr.HTML(_build_processing_bar_html(0))
                processing_elapsed_timer = gr.Markdown("Elapsed: 00:00")
                processing_tick = gr.Timer(value=1.0, active=False)
                cancel_processing_button = gr.Button("Cancel", variant="stop")

        with gr.Column(visible=False) as screen_s5:
            with gr.Row():
                with gr.Column(scale=4):
                    patient_summary_review_panel = gr.HTML("<div class='clarke-card' style='padding:12px;'>No patient selected.</div>")
                with gr.Column(scale=8):
                    review_status_badge = gr.Label(value="Ready for Review", label="Status")
                    review_fhir_values = gr.HTML("<div class='clarke-card'><span class='mono'>FHIR values appear here.</span></div>")
                    with gr.Column(elem_classes=["paper-container"]):
                        section_one_text = gr.Textbox(label="Section 1", lines=5, interactive=True)
                        section_two_text = gr.Textbox(label="Section 2", lines=5, interactive=True)
                        section_three_text = gr.Textbox(label="Section 3", lines=5, interactive=True)
                        section_four_text = gr.Textbox(label="Section 4", lines=5, interactive=True)
                    with gr.Row():
                        sign_off_button = gr.Button("Sign Off & Export", variant="primary")
                        regenerate_button = gr.Button("Regenerate Entire Letter", variant="secondary")

        with gr.Column(visible=False) as screen_s6:
            with gr.Column(elem_classes=["paper-container"]):
                signed_status_badge = gr.Label(value="Signed Off ✓", label="Status")
                signed_letter_markdown = gr.Markdown("### Signed letter will appear here.")
                copy_to_clipboard_text = gr.Textbox(label="Copy to Clipboard", interactive=False, show_copy_button=True)
                download_text_file = gr.File(label="Download as Text")
                next_patient_button = gr.Button("Next Patient", variant="primary")

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
            _start_processing,
            inputs=[app_state, consultation_audio],
            outputs=[
                app_state,
                feedback_text,
                processing_stage,
                processing_progress_bar,
                processing_elapsed_timer,
                processing_tick,
                screen_s1,
                screen_s2,
                screen_s3,
                screen_s4,
                screen_s5,
                screen_s6,
            ],
            show_progress="full",
        )

        processing_tick.tick(
            _poll_processing_progress,
            inputs=[app_state],
            outputs=[
                app_state,
                feedback_text,
                processing_stage,
                processing_progress_bar,
                processing_tick,
                processing_elapsed_timer,
                section_one_text,
                section_two_text,
                section_three_text,
                section_four_text,
                review_fhir_values,
                copy_to_clipboard_text,
                review_status_badge,
                screen_s1,
                screen_s2,
                screen_s3,
                screen_s4,
                screen_s5,
                screen_s6,
            ],
            show_progress="hidden",
        )

        cancel_processing_button.click(
            _cancel_processing,
            inputs=[app_state],
            outputs=[app_state, feedback_text, processing_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6],
            show_progress="hidden",
        )

        regenerate_button.click(
            _regenerate_document,
            inputs=[app_state],
            outputs=[
                app_state,
                feedback_text,
                processing_stage,
                processing_progress_bar,
                processing_elapsed_timer,
                review_status_badge,
                processing_tick,
                screen_s1,
                screen_s2,
                screen_s3,
                screen_s4,
                screen_s5,
                screen_s6,
            ],
            show_progress="full",
        )

        sign_off_button.click(
            _sign_off_document,
            inputs=[app_state, section_one_text, section_two_text, section_three_text, section_four_text],
            outputs=[
                app_state,
                feedback_text,
                signed_letter_markdown,
                signed_status_badge,
                copy_to_clipboard_text,
                download_text_file,
                screen_s1,
                screen_s2,
                screen_s3,
                screen_s4,
                screen_s5,
                screen_s6,
            ],
            show_progress="full",
        )

        next_patient_button.click(
            _next_patient,
            inputs=[app_state],
            outputs=[
                app_state,
                feedback_text,
                section_one_text,
                section_two_text,
                section_three_text,
                section_four_text,
                signed_letter_markdown,
                copy_to_clipboard_text,
                processing_stage,
                processing_elapsed_timer,
                review_status_badge,
                screen_s1,
                screen_s2,
                screen_s3,
                screen_s4,
                screen_s5,
                screen_s6,
            ],
            show_progress="hidden",
        )

    return demo
