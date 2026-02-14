"""Reusable UI components for Clarke frontend screens."""

from __future__ import annotations

from html import escape

import gradio as gr

STATUS_CLASS_MAP: dict[str, str] = {
    "idle": "status-neutral",
    "loading": "status-blue",
    "ready": "status-amber",
    "signed": "status-green",
    "error": "status-red",
}


def build_patient_card(patient: dict) -> gr.HTML:
    """Build a styled patient card component for dashboard rendering.

    Args:
        patient (dict): Patient payload with id, name, age, sex, time, and summary fields.

    Returns:
        gr.HTML: HTML component containing patient card markup.
    """

    patient_id = escape(str(patient.get("id", "")))
    name = escape(str(patient.get("name", "Unknown patient")))
    age = escape(str(patient.get("age", "")))
    sex = escape(str(patient.get("sex", "")))
    appointment_time = escape(str(patient.get("time", "--:--")))
    summary = escape(str(patient.get("summary", "No summary available.")))

    card_html = f"""
    <div class=\"patient-card\" data-patient-id=\"{patient_id}\">
      <p class=\"label\">{appointment_time}</p>
      <h4>{name}</h4>
      <p class=\"caption\">{age} • {sex}</p>
      <p>{summary}</p>
    </div>
    """
    return gr.HTML(card_html)


def build_status_badge(status: str) -> gr.HTML:
    """Build a colour-coded status badge component.

    Args:
        status (str): Logical status token (idle, loading, ready, signed, error).

    Returns:
        gr.HTML: HTML component containing badge markup.
    """

    normalised_status = (status or "idle").strip().lower()
    badge_class = STATUS_CLASS_MAP.get(normalised_status, "status-neutral")
    label = escape(normalised_status.replace("_", " ").title())
    return gr.HTML(f'<span class="status-badge {badge_class}">{label}</span>')
