"""Gradio UI layout for Clarke dashboard and end-to-end consultation flow."""

from __future__ import annotations

import json
import os
import wave
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import gradio as gr
import httpx

from frontend.components import build_dashboard_html, build_global_style_block, build_status_badge_html
from frontend.state import initial_consultation_state, select_patient, show_screen
from frontend.theme import clarke_theme

CLINIC_LIST_PATH = Path("data/clinic_list.json")
API_BASE_URL = os.getenv("CLARKE_API_BASE_URL", "http://127.0.0.1:7860/api/v1")

CLARKE_JS = """
function() {
    if (!document.getElementById('clarke-keyframes')) {
        var style = document.createElement('style');
        style.id = 'clarke-keyframes';
        style.textContent = '@keyframes clarkeGradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }\\n@keyframes clarkeLogoShimmer { 0% { filter: brightness(1); } 50% { filter: brightness(1.3); } 100% { filter: brightness(1); } }';
        document.head.appendChild(style);
    }

    function stripGradioPadding() {
        var app = document.querySelector('gradio-app');
        if (app) {
            app.style.setProperty('background', 'linear-gradient(135deg, #0A0E1A 0%, #1E3A8A 15%, #4A1942 25%, #8B2040 35%, #C4522A 45%, #D4AF37 55%, #E8C84A 65%, #F0E0A0 78%, #F8F6F1 92%, #F8F6F1 100%)', 'important');
            app.style.setProperty('background-size', '200% 200%', 'important');
            app.style.setProperty('animation', 'clarkeGradientShift 15s ease-in-out infinite', 'important');
            app.style.setProperty('padding', '0', 'important');
            app.style.setProperty('margin', '0', 'important');
            app.style.setProperty('overflow-x', 'hidden', 'important');
        }

        document.querySelectorAll('.gradio-container, [class*="gradio-container-"]').forEach(function(el) {
            el.style.setProperty('max-width', '100%', 'important');
            el.style.setProperty('width', '100%', 'important');
            el.style.setProperty('min-height', '100vh', 'important');
            el.style.setProperty('padding', '0', 'important');
            el.style.setProperty('margin', '0', 'important');
            el.style.setProperty('background', 'transparent', 'important');
        });

        document.querySelectorAll('.main, .wrap, .contain, [class*="column"], [class*="gap"]').forEach(function(el) {
            el.style.setProperty('max-width', '100%', 'important');
            el.style.setProperty('padding', '0', 'important');
            el.style.setProperty('gap', '0', 'important');
            el.style.setProperty('margin', '0', 'important');
        });

        document.body.style.setProperty('margin', '0', 'important');
        document.body.style.setProperty('padding', '0', 'important');
        document.body.style.setProperty('overflow-x', 'hidden', 'important');
        document.body.style.setProperty('background', '#F8F6F1', 'important');

        var footer = document.querySelector('footer');
        if (footer) footer.style.setProperty('display', 'none', 'important');
    }

    stripGradioPadding();
    [100, 300, 500, 1000, 2000, 3000, 5000].forEach(function(ms) {
        setTimeout(stripGradioPadding, ms);
    });

    var observer = new MutationObserver(function() { stripGradioPadding(); });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });
    console.log('Clarke: MutationObserver installed for full-screen layout');

    setTimeout(function() {
        var ids = ['hidden-select-0','hidden-select-1','hidden-select-2','hidden-select-3','hidden-select-4',
                   'hidden-start-consultation','hidden-end-consultation','hidden-sign-off','hidden-next-patient','hidden-back',
                   'hidden-review-letter','hidden-cancel','hidden-regenerate','hidden-copy','hidden-download'];
        ids.forEach(function(id) {
            var el = document.getElementById(id);
            if (el) {
                el.style.cssText = 'position:fixed!important;top:-9999px!important;left:-9999px!important;width:1px!important;height:1px!important;opacity:0!important;';
                var p = el.parentElement;
                for (var i = 0; i < 3 && p && p.tagName === 'DIV'; i++) {
                    if (p.children.length <= 2) {
                        p.style.cssText = 'position:fixed!important;top:-9999px!important;left:-9999px!important;width:1px!important;height:1px!important;opacity:0!important;overflow:hidden!important;';
                    }
                    p = p.parentElement;
                }
            }
        });
        console.log('Clarke: Bridge buttons hidden');
    }, 500);
}
"""

MOCK_PATIENT_CONTEXTS: dict[int, dict[str, Any]] = {
    0: {
        "name": "Mrs. Margaret Thompson",
        "age": 67,
        "sex": "Female",
        "dob": "15/03/1958",
        "nhs": "943 476 2185",
        "problems": ["Type 2 Diabetes Mellitus (E11.9)", "Essential Hypertension (I10)", "Hyperlipidaemia (E78.5)"],
        "medications": ["Metformin 1g BD", "Lisinopril 10mg OD", "Atorvastatin 20mg ON", "Aspirin 75mg OD"],
        "allergies": [{"name": "Penicillin", "reaction": "Anaphylaxis", "severity": "severe"}],
        "labs": [
            {"test": "HbA1c", "value": "8.2%", "trend": "↑", "note": "target <7.0%", "date": "28/01/2026"},
            {"test": "eGFR", "value": "68 mL/min", "trend": "↓", "note": "prev 72", "date": "28/01/2026"},
            {"test": "Creatinine", "value": "98 µmol/L", "trend": "", "note": "", "date": "28/01/2026"},
        ],
    },
    1: {
        "name": "Mr. Emeka Okafor",
        "age": 54,
        "sex": "Male",
        "dob": "22/07/1971",
        "nhs": "621 839 4057",
        "problems": ["Coronary Artery Disease (I25.1)", "Post-PCI (Z95.5)", "Type 2 Diabetes (E11.9)"],
        "medications": ["Clopidogrel 75mg OD", "Bisoprolol 5mg OD", "Atorvastatin 80mg ON", "Ramipril 5mg OD", "GTN spray PRN"],
        "allergies": [],
        "labs": [
            {"test": "Troponin I", "value": "<0.01 ng/mL", "trend": "", "note": "normal", "date": "05/02/2026"},
            {"test": "Total Cholesterol", "value": "4.2 mmol/L", "trend": "↓", "note": "prev 5.1", "date": "05/02/2026"},
            {"test": "HbA1c", "value": "7.1%", "trend": "", "note": "at target", "date": "10/01/2026"},
        ],
    },
    2: {
        "name": "Ms. Priya Patel",
        "age": 28,
        "sex": "Female",
        "dob": "03/11/1997",
        "nhs": "754 213 8690",
        "problems": ["Asthma (J45.9) — poorly controlled", "Allergic Rhinitis (J30.1)"],
        "medications": ["Salbutamol 100µg MDI PRN", "Beclometasone 200µg BD", "Montelukast 10mg ON", "Cetirizine 10mg OD"],
        "allergies": [{"name": "NSAIDs", "reaction": "Bronchospasm", "severity": "moderate"}],
        "labs": [
            {"test": "Peak Flow", "value": "320 L/min", "trend": "↓", "note": "predicted 450", "date": "01/02/2026"},
            {"test": "Eosinophils", "value": "0.6 × 10⁹/L", "trend": "↑", "note": "elevated", "date": "01/02/2026"},
        ],
    },
    3: {
        "name": "Mr. David Williams",
        "age": 72,
        "sex": "Male",
        "dob": "19/06/1953",
        "nhs": "482 917 3564",
        "problems": ["Heart Failure with reduced EF (I50.2)", "Atrial Fibrillation (I48.0)", "CKD Stage 3 (N18.3)"],
        "medications": ["Furosemide 40mg OD", "Ramipril 2.5mg OD", "Bisoprolol 2.5mg OD", "Apixaban 5mg BD", "Spironolactone 25mg OD"],
        "allergies": [{"name": "ACE inhibitor cough", "reaction": "Persistent dry cough", "severity": "mild"}],
        "labs": [
            {"test": "BNP", "value": "890 pg/mL", "trend": "↑", "note": "prev 450", "date": "10/02/2026"},
            {"test": "eGFR", "value": "38 mL/min", "trend": "↓", "note": "prev 45", "date": "10/02/2026"},
            {"test": "K+", "value": "5.1 mmol/L", "trend": "↑", "note": "monitor", "date": "10/02/2026"},
        ],
    },
    4: {
        "name": "Mrs. Fatima Khan",
        "age": 45,
        "sex": "Female",
        "dob": "08/09/1980",
        "nhs": "318 645 7923",
        "problems": ["Major Depressive Disorder (F32.1)", "Generalised Anxiety Disorder (F41.1)", "Vitamin D Deficiency (E55.9)"],
        "medications": ["Sertraline 100mg OD", "Vitamin D3 800 IU OD", "Zopiclone 3.75mg PRN"],
        "allergies": [],
        "labs": [
            {"test": "TSH", "value": "2.1 mIU/L", "trend": "", "note": "normal", "date": "20/01/2026"},
            {"test": "Vitamin D", "value": "32 nmol/L", "trend": "↑", "note": "prev 18, improving", "date": "20/01/2026"},
            {"test": "FBC", "value": "Normal", "trend": "", "note": "", "date": "20/01/2026"},
        ],
    },
}


def _hidden_click_js(elem_id: str, action_label: str) -> str:
    """Return debug-friendly JS snippet that clicks hidden Gradio wrappers.

    Args:
        elem_id (str): DOM id assigned via the hidden button `elem_id`.
        action_label (str): Human-readable action label for console diagnostics.

    Returns:
        str: Inline JavaScript for HTML onclick handlers.
    """

    return (
        "(function(){"
        f"console.log('Clarke: {action_label} button clicked');"
        f"var el=document.getElementById('{elem_id}');"
        "console.log('Clarke: Found element:', el);"
        "if(!el){"
        f"console.error('Clarke: Element #{elem_id} not found in DOM');"
        "return;"
        "}"
        "if(el.tagName==='BUTTON'){"
        "el.click();"
        "console.log('Clarke: Clicked element directly (it IS the button)');"
        "}else{"
        "var btn=el.querySelector('button');"
        "if(btn){"
        "btn.click();"
        "console.log('Clarke: Clicked inner button');"
        "}else{"
        f"console.error('Clarke: No clickable button found for #{elem_id}');"
        "}"
        "}"
        "})()"
    )


def load_clinic_list(path: Path = CLINIC_LIST_PATH) -> dict[str, Any]:
    """Load clinic list data for dashboard rendering.

    Args:
        path (Path): Path to clinic roster JSON file.

    Returns:
        dict[str, Any]: Clinic metadata and patient list payload.
    """

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def _trend_symbol(trend: str) -> str:
    """Map trend labels to compact visual symbols."""

    trend_l = (trend or "").strip().lower()
    if trend_l in {"rising", "up", "↑"}:
        return "<span style='color:#c0392b;font-weight:600;'> ↑</span>"
    if trend_l in {"falling", "down", "↓"}:
        return "<span style='color:#27ae60;font-weight:600;'> ↓</span>"
    return "<span style='color:#555;'> →</span>"


def _safe_datetime_from_iso(value: Any) -> datetime:
    """Parse datetime safely, avoiding None/'None' isoformat errors."""

    raw_value = str(value).strip() if value is not None else ""
    if not raw_value or raw_value == "None":
        return datetime.now(tz=timezone.utc)
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return datetime.now(tz=timezone.utc)


def _mock_context_for_index(patient_index: int) -> dict[str, Any]:
    """Build frontend mock patient context for deterministic S2 rendering."""

    payload = MOCK_PATIENT_CONTEXTS.get(patient_index, MOCK_PATIENT_CONTEXTS[0])
    return {
        "demographics": {
            "name": payload["name"],
            "age": payload["age"],
            "sex": payload["sex"],
            "dob": payload["dob"],
            "nhs_number": payload["nhs"],
        },
        "problem_list": payload["problems"],
        "medications": [
            {"name": med, "dose": "", "frequency": ""} for med in payload["medications"]
        ],
        "allergies": [
            {"substance": item["name"], "reaction": f"{item['reaction']} ({item['severity']})"}
            for item in payload["allergies"]
        ],
        "recent_labs": [
            {
                "name": lab["test"],
                "value": lab["value"],
                "unit": "",
                "trend": lab["trend"],
                "date": lab["date"],
                "note": lab["note"],
            }
            for lab in payload["labs"]
        ],
    }


def _format_patient_context_html(context: dict[str, Any]) -> str:
    """Render patient context cards for S2 inside a unified content block."""

    demographics = context.get("demographics", {})
    problem_list = context.get("problem_list", [])
    medications = context.get("medications", [])
    allergies = context.get("allergies", [])
    labs = context.get("recent_labs", [])

    age = demographics.get("age")
    demo_items = [
        f"<p style='margin:4px 0;color:#1A1A2E;font-family:Inter,sans-serif;'>{escape(str(demographics.get('name', 'Unknown')))}</p>",
        f"<p style='margin:4px 0;color:#555;font-family:Inter,sans-serif;'>{escape(str(age if age is not None else 'N/A'))} · {escape(str(demographics.get('sex', 'N/A')))}</p>",
        f"<p style='margin:4px 0;color:#555;font-family:Inter,sans-serif;'>DOB: {escape(str(demographics.get('dob', 'N/A')))}</p>",
        f"<p style='margin:4px 0;color:#555;font-family:Inter,sans-serif;'>NHS: {escape(str(demographics.get('nhs_number', 'N/A')))}</p>",
    ]

    def _card(title: str, body: str, span_two: bool = False) -> str:
        span_style = "grid-column:span 2;" if span_two else ""
        return (
            "<div style='background:rgba(255,255,255,0.72);backdrop-filter:blur(8px);border-radius:12px;"
            "padding:20px;border:1px solid rgba(212,175,55,0.15);" + span_style + "'>"
            f"<h3 style='color:#D4AF37;font-size:14px;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px 0;font-family:Inter,sans-serif;'>{title}</h3>{body}</div>"
        )

    problems = "".join(f"<p style='margin:4px 0;color:#1A1A2E;font-family:Inter,sans-serif;'>{escape(str(item))}</p>" for item in problem_list) or "<p style='margin:4px 0;color:#555;font-family:Inter,sans-serif;'>No active problems</p>"
    meds = "".join(
        f"<p style=\"margin:4px 0;color:#1A1A2E;font-family:'JetBrains Mono',monospace;font-size:13px;\">{escape(str(m.get('name', 'Medication')))} {escape(str(m.get('dose', '')))} {escape(str(m.get('frequency', '')))}</p>"
        for m in medications
    ) or "<p style='margin:4px 0;color:#555;font-family:Inter,sans-serif;'>None documented</p>"
    allergy_markup = "".join(
        f"<p style='margin:4px 0;color:#c0392b;font-family:Inter,sans-serif;'>⚠ {escape(str(a.get('substance', 'Unknown')))} — {escape(str(a.get('reaction', 'Reaction not recorded')))}</p>"
        for a in allergies
    ) or "<p style='margin:4px 0;color:#555;font-family:Inter,sans-serif;'>No known allergies</p>"
    lab_markup = "".join(
        f"<p style=\"margin:4px 0;color:#1A1A2E;font-family:'JetBrains Mono',monospace;font-size:13px;\">{escape(str(l.get('name', 'Lab')))}: {escape(str(l.get('value', '')))} {escape(str(l.get('unit', '')))}{_trend_symbol(str(l.get('trend', 'stable')))}</p>"
        for l in labs
    ) or "<p style='margin:4px 0;color:#555;font-family:Inter,sans-serif;'>No recent labs</p>"

    return "".join(
        [
            _card("Demographics", "".join(demo_items)),
            _card("Problem List", problems),
            _card("Medications", meds),
            _card("Allergies", allergy_markup),
            _card("Recent Labs", lab_markup, span_two=True),
        ]
    )


def _context_screen_html(patient: dict[str, Any], context: dict[str, Any]) -> str:
    """Build S2 shell + actions + context in one full-screen HTML block."""

    name = escape(str(patient.get("name", "Patient")))
    context_cards = _format_patient_context_html(context)
    return f"""<div style="min-height:100vh;background:#F8F6F1;padding:32px 48px;margin:0;"><h2 style="font-family:'DM Serif Display',serif;color:#1A1A2E;margin:0 0 16px 0;">Patient Context — {name}</h2><div style="display:flex;gap:12px;margin-bottom:24px;"><button onclick="{_hidden_click_js('hidden-start-consultation', 'Start Consultation')}" class="clarke-btn-gold">Start Consultation</button><button onclick="{_hidden_click_js('hidden-back', 'Back to Dashboard')}" class="clarke-btn-secondary">← Back to Dashboard</button></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">{context_cards}</div></div>"""

def _recording_screen_html(timer_text: str) -> str:
    """Render S3 recording screen in full-screen warm-white layout."""

    return f"""<div style="min-height:100vh;background:#F8F6F1;padding:32px 48px;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;"><div style="display:inline-block;width:24px;height:24px;background:#D4AF37;border-radius:50%;animation:recordPulse 2s ease-in-out infinite;margin-bottom:16px;"></div><div style="font-family:Inter,sans-serif;font-size:13px;font-weight:600;color:#D4AF37;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:24px;">Recording</div><div style="font-family:'JetBrains Mono',monospace;font-size:56px;color:#1A1A2E;letter-spacing:0.05em;">{escape(timer_text)}</div></div>"""

def _processing_screen_html(stage_number: int, stage_label: str, stage_description: str, elapsed: str) -> str:
    """Render S4 processing screen in full-screen warm-white layout."""

    return f"""<div style="min-height:100vh;background:#F8F6F1;padding:32px 48px;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;"><div style="position:relative;width:140px;height:140px;margin-bottom:40px;"><div style="position:absolute;top:0;left:0;width:140px;height:140px;border:3px solid rgba(30,58,138,0.15);border-top:3px solid #D4AF37;border-radius:50%;animation:progressSpin 1.5s linear infinite;"></div><div style="position:absolute;top:10px;left:10px;width:120px;height:120px;border:2px solid rgba(212,175,55,0.15);border-radius:50%;animation:progressGlow 2s ease-in-out infinite;"></div><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-family:'DM Serif Display',serif;font-size:36px;color:#D4AF37;">{stage_number}/3</div></div><div style="font-family:Inter,sans-serif;font-size:18px;color:#1A1A2E;font-weight:500;margin-bottom:8px;">{escape(stage_label)}</div><div style="font-family:Inter,sans-serif;font-size:14px;color:#555;">{escape(stage_description)}</div><div style="font-family:'JetBrains Mono',monospace;font-size:14px;color:#555;margin-top:24px;">{escape(elapsed)}</div><button onclick="{_hidden_click_js('hidden-cancel', 'Cancel Processing')}" class="clarke-btn-secondary" style="margin-top:24px;">Cancel</button></div>"""

def _build_generated_document(state: dict[str, Any]) -> dict[str, Any]:
    """Create an NHS-format clinic letter for S5/S6 review."""

    selected_patient = (state or {}).get("selected_patient") or {}
    patient_context = (state or {}).get("patient_context") or {}
    demographics = patient_context.get("demographics", {})
    labs = patient_context.get("recent_labs", [])
    problems = patient_context.get("problem_list", [])
    meds = patient_context.get("medications", [])

    patient_name = str(demographics.get("name") or selected_patient.get("name") or "Patient")
    dob = str(demographics.get("dob") or "Unknown")
    nhs = str(demographics.get("nhs_number") or "Unknown")
    today = datetime.now().strftime("%d %B %Y")
    gp_name = "Andrew Wilson"
    address = "Riverside Medical Practice\n14 Harcourt Street\nLondon"

    investigations = "\n".join(
        f"- {lab.get('name', 'Test')}: {lab.get('value', '')} {lab.get('unit', '')} ({lab.get('date', '')})".strip()
        for lab in labs
    ) or "- No recent investigations available"
    medication_line = ", ".join(m.get("name", "") for m in meds if m.get("name"))
    main_problem = problems[0] if problems else "ongoing clinical concerns"

    if "Margaret Thompson" in patient_name:
        history = "She attended for diabetes and cardiovascular risk review with persistent hyperglycaemia despite current therapy. She reports reduced activity tolerance and occasional post-prandial fatigue over recent weeks."
        assessment = "Suboptimal glycaemic control with HbA1c 8.2% in the context of known type 2 diabetes, hypertension, and hyperlipidaemia. Renal function remains acceptable but trending down."
        plan_lines = [
            "Increase metformin optimisation counselling and initiate structured diabetic diet support.",
            "Arrange repeat HbA1c, renal profile, and urine ACR in 8 weeks.",
            "Continue lisinopril/atorvastatin/aspirin and monitor blood pressure weekly.",
        ]
    else:
        history = f"I reviewed {patient_name} regarding {main_problem.lower()} and ongoing symptom burden in clinic. The patient reports variable day-to-day control and is keen for treatment optimisation."
        assessment = f"Current presentation is consistent with {main_problem.lower()}, requiring continued medication review and follow-up."
        plan_lines = [
            "Continue current treatment with safety-netting advice.",
            "Repeat key blood tests prior to next follow-up.",
            "Review in specialist clinic to reassess response and escalation needs.",
        ]

    letter_text = (
        f"{today}\n\n"
        f"Dr {gp_name}\n"
        f"{address}\n\n"
        f"Dear Dr {gp_name},\n\n"
        f"Re: {patient_name} (DOB: {dob}, NHS: {nhs})\n"
        f"    {address}\n\n"
        f"Thank you for referring / I reviewed {patient_name} in General Practice Clinic on {today}.\n\n"
        "History of Presenting Complaint\n"
        f"{history}\n\n"
        "Examination\n"
        "The patient was comfortable at rest, haemodynamically stable, and clinically euvolaemic on examination. No acute red-flag findings were identified today.\n\n"
        "Investigations\n"
        f"{investigations}\n\n"
        "Assessment\n"
        f"{assessment}\n\n"
        "Plan\n"
        + "\n".join(f"{i + 1}. {line}" for i, line in enumerate(plan_lines))
        + f"\n\nI will review {patient_name} in 8 weeks. Please do not hesitate to contact us if there are any concerns in the interim.\n\n"
        "Yours sincerely,\n\n"
        "Dr Sarah Chen\n"
        "Consultant, General Practice\n"
        "Clarke NHS Trust"
    )

    sections = [
        {"heading": "NHS Clinic Letter", "content": letter_text},
        {"heading": "Clinical Issues", "content": "\n".join(f"- {item}" for item in problems) or "- None listed"},
        {"heading": "Current Medications", "content": medication_line or "None documented"},
        {"heading": "Follow-up", "content": "Review in 8 weeks with repeat investigations."},
    ]
    return {
        "title": "NHS Clinic Letter",
        "status": "ready_for_review",
        "sections": sections,
        "patient_name": patient_name,
        "nhs_number": nhs,
    }


def _render_letter_sections(letter_sections: list[dict[str, str]]) -> tuple[str, str, str, str]:
    """Map generated letter sections onto fixed textbox outputs.

    Args:
        letter_sections (list[dict[str, str]]): Ordered letter sections.

    Returns:
        tuple[str, str, str, str]: Four section strings for review textboxes.
    """

    resolved = list(letter_sections)
    while len(resolved) < 4:
        resolved.append({"heading": f"Section {len(resolved) + 1}", "content": ""})
    return tuple(f"{s.get('heading', '')}\n{s.get('content', '').strip()}".strip() for s in resolved[:4])


def _handle_patient_selection(state: dict[str, Any], patient_index: int):
    """Update state and call backend context endpoint when a patient index is selected.

    Args:
        state (dict[str, Any]): Current UI session state.
        patient_index (int): Selected patient index from the dashboard.

    Returns:
        tuple[...]: Updated state, feedback, context HTML, context shell HTML, and visibility updates.
    """

    clinic_payload = load_clinic_list()
    patients = clinic_payload.get("patients", [])
    if patient_index < 0 or patient_index >= len(patients):
        return state, "Patient selection failed: patient index out of range.", _context_screen_html({}, {}), "", "", "", "", "", gr.update(), *show_screen("s1")

    patient = patients[patient_index]
    updated_state = select_patient(state, patient)
    updated_state['current_patient_index'] = patient_index
    patient_id = str(patient.get("id", ""))
    if os.getenv("USE_MOCK_FHIR", "").lower() == "true":
        context = _mock_context_for_index(patient_index)
        feedback = f"Loaded mock patient context for {patient['name']} ({patient_id})."
    else:
        try:
            context = _api_request("POST", f"/patients/{patient_id}/context")
        except Exception as exc:
            context = _mock_context_for_index(patient_index)
            feedback = f"Patient selected with frontend mock context fallback: {exc}"
        else:
            feedback = f"Loaded patient context for {patient['name']} ({patient_id})."

    updated_state["patient_context"] = context

    completed_patients = set(updated_state.get("completed_patients", []))
    if patient_index in completed_patients:
        generated = updated_state.get("signed_letters", {}).get(str(patient_index), "")
        if generated:
            updated_state["signed_document_text"] = generated
            updated_state["screen"] = "s5"
            return updated_state, f"Opened completed patient {patient['name']} in Document Review.", _context_screen_html(patient, context), generated, "", "", "", f"<div style='min-height:100vh;background:#F8F6F1;padding:24px 48px 48px 48px;margin:0;'><div style='font-family:Inter,sans-serif;font-size:16px;line-height:1.75;color:#1A1A2E;white-space:pre-wrap;' id='signed-letter-text'>{escape(generated)}</div></div>", "<span style='font-family:Inter,sans-serif;'>Previously signed letter loaded for review.</span>", *show_screen("s5")

    return updated_state, feedback, _context_screen_html(patient, context), "", "", "", "", "", gr.update(), *show_screen("s2")


def _handle_back_to_dashboard(state):
    """Navigate from context screen back to dashboard.

    Args:
        state (dict[str, Any]): Current application state.

    Returns:
        tuple[...]: Updated state, feedback text, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s1"
    return updated_state, "Returned to dashboard.", *show_screen("s1")


def _handle_start_consultation(state):
    """Start consultation by calling backend and storing consultation ID.

    Args:
        state (dict[str, Any]): Current application state.

    Returns:
        tuple[...]: Updated state, feedback, recording HTML, timer tick update, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    patient_id = str((updated_state.get("selected_patient") or {}).get("id", ""))
    if not patient_id:
        return updated_state, "Please select a patient first.", _recording_screen_html("00:00"), gr.update(active=False), *show_screen("s1")

    try:
        payload = _api_request("POST", "/consultations/start", json={"patient_id": patient_id})
    except Exception as exc:
        return updated_state, f"Failed to start consultation: {exc}", _recording_screen_html("00:00"), gr.update(active=False), *show_screen("s2")

    updated_state["consultation"] = {"id": payload.get("consultation_id"), "status": payload.get("status", "recording")}
    updated_state["recording_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["screen"] = "s3"
    return updated_state, "Consultation recording started.", _recording_screen_html("00:00"), gr.update(active=True), *show_screen("s3")


def _update_recording_timer(state):
    """Compute MM:SS elapsed timer value for the active consultation recording.

    Args:
        state (dict[str, Any]): Current UI state containing recording start metadata.

    Returns:
        str: HTML with elapsed timer.
    """

    started_at = str((state or {}).get("recording_started_at", "")).strip()
    if not started_at:
        return _recording_screen_html("00:00")
    elapsed_s = max(int((datetime.now(tz=timezone.utc) - _safe_datetime_from_iso(started_at)).total_seconds()), 0)
    minutes, seconds = divmod(elapsed_s, 60)
    return _recording_screen_html(f"{minutes:02d}:{seconds:02d}")


def _stage_from_pipeline(stage: str) -> tuple[int, str, str]:
    """Map backend pipeline stage to display values.

    Args:
        stage (str): Backend pipeline stage value.

    Returns:
        tuple[int, str, str]: Stage number, label, and description.
    """

    mapping = {
        "transcribing": (1, "Finalising transcript…", "MedASR processing audio"),
        "retrieving_context": (2, "Synthesising patient context…", "MedGemma 4B querying records"),
        "generating_document": (3, "Generating clinical letter…", "MedGemma 27B composing document"),
        "complete": (3, "Generating clinical letter…", "MedGemma 27B composing document"),
    }
    return mapping.get(stage, mapping["transcribing"])




def _ensure_mock_audio_file(audio_path: str | None) -> str | None:
    """Create a short silent WAV when running in mock mode and no audio was captured."""

    if audio_path:
        return audio_path
    if os.getenv("MEDASR_MODEL_ID", "").lower() != "mock":
        return None

    upload_dir = Path("data/uploads/mock")
    upload_dir.mkdir(parents=True, exist_ok=True)
    silent_path = upload_dir / "silent.wav"
    with wave.open(str(silent_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * (16000 * 6))
    return str(silent_path)


def _start_processing(state, audio_path):
    """Upload audio and end consultation, then transition to processing screen.

    Args:
        state (dict[str, Any]): Current UI state.
        audio_path (str | None): File path returned by Gradio audio component.

    Returns:
        tuple[...]: Updated state, feedback, processing HTML, timer update, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    consultation_id = str((updated_state.get("consultation") or {}).get("id", ""))
    if not consultation_id:
        return updated_state, "Consultation session is missing. Start consultation again.", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"), gr.update(active=False), *show_screen("s3")

    resolved_audio_path = _ensure_mock_audio_file(audio_path)
    if not resolved_audio_path:
        return updated_state, "Please capture audio before ending consultation.", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"), gr.update(active=False), *show_screen("s3")

    if os.getenv("MEDASR_MODEL_ID", "").lower() == "mock":
        updated_state["captured_audio_path"] = resolved_audio_path
        updated_state["processing_started_at"] = datetime.now(tz=timezone.utc).isoformat()
        updated_state["consultation"] = updated_state.get("consultation") or {}
        updated_state["consultation"]["id"] = ""
        updated_state["consultation"]["status"] = "processing"
        updated_state["screen"] = "s4"
        return updated_state, "Consultation ended. Processing audio and generating document.", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"), gr.update(active=True), *show_screen("s4")

    try:
        with Path(resolved_audio_path).open("rb") as stream:
            _api_request("POST", f"/consultations/{consultation_id}/audio", files={"audio_file": (Path(resolved_audio_path).name, stream, "audio/wav")}, data={"is_final": "true"}, timeout=120.0)
        _api_request("POST", f"/consultations/{consultation_id}/end", timeout=180.0)
    except Exception as exc:
        return updated_state, f"Failed to end consultation: {exc}", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"), gr.update(active=False), *show_screen("s3")

    updated_state["captured_audio_path"] = resolved_audio_path
    updated_state["processing_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["consultation"]["status"] = "processing"
    updated_state["screen"] = "s4"
    return updated_state, "Consultation ended. Processing audio and generating document.", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"), gr.update(active=True), *show_screen("s4")


def _poll_processing_progress(state):
    """Poll backend consultation progress and transition to review when complete.

    Args:
        state (dict[str, Any]): Current state containing consultation metadata.

    Returns:
        tuple[...]: Updated state and UI updates for processing/review screens.
    """

    updated_state = dict(state or initial_consultation_state())
    consultation_id = str((updated_state.get("consultation") or {}).get("id", ""))
    started_at = str(updated_state.get("processing_started_at", "") or "")
    elapsed = "Elapsed: 00:00"
    if started_at:
        elapsed_s = max(int((datetime.now(tz=timezone.utc) - _safe_datetime_from_iso(started_at)).total_seconds()), 0)
        minutes, seconds = divmod(elapsed_s, 60)
        elapsed = f"Elapsed: {minutes:02d}:{seconds:02d}"

    if not consultation_id:
        doc = _build_generated_document(updated_state)
        updated_state["generated_document"] = doc
        updated_state["consultation"] = updated_state.get("consultation") or {"id": None, "status": "review"}
        updated_state["consultation"]["status"] = "review"
        updated_state["screen"] = "s5"
        s1, s2, s3, s4 = _render_letter_sections(doc.get("sections", []))
        fhir = ""
        return updated_state, "Processing complete. Review the generated clinic letter.", _processing_screen_html(3, "Generating clinical letter…", "MedGemma 27B composing document", elapsed), gr.update(active=False), s1, s2, s3, s4, fhir, *show_screen("s5")

    try:
        progress = _api_request("GET", f"/consultations/{consultation_id}/progress")
    except Exception as exc:
        return updated_state, f"Progress polling failed: {exc}", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", elapsed), gr.update(active=False), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), *show_screen("s4")

    stage_number, stage_label, stage_description = _stage_from_pipeline(str(progress.get("stage", "transcribing")))
    if str(progress.get("stage", "")) != "complete":
        return updated_state, f"Processing in progress: {stage_label}", _processing_screen_html(stage_number, stage_label, stage_description, elapsed), gr.update(active=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), *show_screen("s4")

    document_payload = _api_request("GET", f"/consultations/{consultation_id}/document").get("document") or _build_generated_document(updated_state)
    updated_state["generated_document"] = document_payload
    updated_state["consultation"]["status"] = "review"
    updated_state["screen"] = "s5"
    s1, s2, s3, s4 = _render_letter_sections(document_payload.get("sections", []))
    fhir = "<br>".join(
        [
            f"<span style='font-family:JetBrains Mono,monospace;font-size:14px;background:rgba(212,175,55,0.1);padding:2px 6px;border-radius:4px;color:#1E3A8A;'>NHS: {escape(str(document_payload.get('nhs_number', 'N/A')))}</span>",
            f"<span style='font-family:JetBrains Mono,monospace;font-size:14px;background:rgba(212,175,55,0.1);padding:2px 6px;border-radius:4px;color:#1E3A8A;'>Patient: {escape(str(document_payload.get('patient_name', 'N/A')))}</span>",
        ]
    )
    return updated_state, "Processing complete. Review the generated clinic letter.", _processing_screen_html(3, "Generating clinical letter…", "MedGemma 27B composing document", elapsed), gr.update(active=False), s1, s2, s3, s4, fhir, *show_screen("s5")


def _regenerate_document(state):
    """Restart processing view before polling backend completion status again.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[...]: Updated state and screen visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["processing_started_at"] = datetime.now(tz=timezone.utc).isoformat()
    updated_state["consultation"]["status"] = "processing"
    updated_state["screen"] = "s4"
    return updated_state, "Regenerating entire clinic letter.", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"), gr.update(active=True), *show_screen("s4")


def _cancel_processing(state):
    """Cancel processing workflow and return to live consultation screen.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[...]: Updated state, feedback, and visibility updates.
    """

    updated_state = dict(state or initial_consultation_state())
    updated_state["screen"] = "s3"
    updated_state["consultation"]["status"] = "recording"
    return updated_state, "Processing cancelled. Returned to consultation.", gr.update(active=False), *show_screen("s3")


def _sign_off_document(state, section_1, section_2, section_3, section_4):
    """Persist edited sections to backend sign-off endpoint and show final letter.

    Args:
        state (dict[str, Any]): Current UI state.
        section_1 (str): Edited section one text.
        section_2 (str): Edited section two text.
        section_3 (str): Edited section three text.
        section_4 (str): Edited section four text.

    Returns:
        tuple[...]: Updated state and signed-off UI content.
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
            return updated_state, f"Sign-off failed: {exc}", gr.update(), "", gr.update(), *show_screen("s5")

    signed_letter = "\n\n".join(part.strip() for part in edited_sections if part and part.strip())
    
    updated_state["signed_document_text"] = signed_letter
    selected_index = int(updated_state.get('current_patient_index', 0))
    signed_letters = dict(updated_state.get('signed_letters', {}))
    signed_letters[str(selected_index)] = signed_letter
    updated_state['signed_letters'] = signed_letters
    updated_state["consultation"]["status"] = "signed_off"
    updated_state["screen"] = "s6"
    export_path = Path("data") / "demo" / "latest_signed_letter.txt"
    export_path.write_text(signed_letter + "\n", encoding="utf-8")
    signed_html = f"<div style='min-height:100vh;background:#F8F6F1;padding:24px 48px 48px 48px;margin:0;'><div style='font-family:Inter,sans-serif;font-size:16px;line-height:1.75;color:#1A1A2E;white-space:pre-wrap;' id='signed-letter-text'>{escape(signed_letter)}</div></div>"
    return updated_state, "Document signed off. You can now copy or download the letter.", signed_html, signed_letter, gr.update(value=str(export_path)), *show_screen("s6")



def _copy_signed_document(state):
    """Refresh copy textbox payload for signed letter actions.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, str]: State, status message, and copy text payload.
    """

    updated_state = dict(state or initial_consultation_state())
    signed_text = str(updated_state.get("signed_document_text") or "")
    if not signed_text:
        return updated_state, "No signed letter available to copy yet.", ""
    return updated_state, "Letter content refreshed for copy.", signed_text


def _prepare_signed_download(state):
    """Refresh downloadable signed-letter text artifact.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[dict[str, Any], str, Any]: State, status message, and file update.
    """

    updated_state = dict(state or initial_consultation_state())
    signed_text = str(updated_state.get("signed_document_text") or "")
    if not signed_text:
        return updated_state, "No signed letter available to download yet.", gr.update(value=None)

    export_path = Path("data") / "demo" / "latest_signed_letter.txt"
    export_path.write_text(signed_text + "\n", encoding="utf-8")
    return updated_state, "Download file refreshed.", gr.update(value=str(export_path))

def _next_patient(state):
    """Reset consultation workflow and return to dashboard after sign-off.

    Args:
        state (dict[str, Any]): Current UI state.

    Returns:
        tuple[...]: Reset state and cleared UI content updates.
    """

    updated_state = dict(state or initial_consultation_state())
    completed = set(updated_state.get('completed_patients', []))
    current_index = int(updated_state.get('current_patient_index', 0))
    completed.add(current_index)
    updated_state['completed_patients'] = sorted(completed)
    dashboard = build_dashboard_html(load_clinic_list(), completed_patients=updated_state['completed_patients'])

    refreshed_state = initial_consultation_state()
    refreshed_state['completed_patients'] = updated_state['completed_patients']
    refreshed_state['signed_letters'] = dict(updated_state.get('signed_letters', {}))
    return refreshed_state, "Ready for next patient. Please select a patient card.", "", "", "", "", "", "", dashboard, *show_screen("s1")


def build_ui() -> gr.Blocks:
    """Build the primary Clarke UI blocks for the dashboard flow.

    Args:
        None: Function reads local static assets and clinic JSON data.

    Returns:
        gr.Blocks: Configured Gradio Blocks application.
    """

    clinic_payload = load_clinic_list()

    with gr.Blocks(theme=clarke_theme, css=Path("frontend/assets/style.css").read_text(encoding="utf-8"), title="Clarke", js=CLARKE_JS) as demo:
        app_state = gr.State(initial_consultation_state())
        gr.HTML(build_global_style_block())
        feedback_text = gr.Markdown("", visible=False)

        with gr.Column(visible=False) as screen_s2:
            context_screen_html = gr.HTML(_context_screen_html({}, {}))
            hidden_start_button = gr.Button("hidden-start-consultation", visible=True, elem_id="hidden-start-consultation")
            hidden_back_button = gr.Button("hidden-back", visible=True, elem_id="hidden-back")

        with gr.Column(visible=False) as screen_s3:
            recording_html = gr.HTML(_recording_screen_html("00:00"))
            consultation_audio = gr.Audio(sources=["microphone"], streaming=False, type="filepath", label="Consultation Audio", elem_id="clarke-audio-input")
            recording_tick = gr.Timer(value=1.0, active=False)
            gr.HTML("""<div style='position:sticky; bottom:0; left:0; right:0; z-index:100;'><button onclick=\"(function(){var el=document.getElementById('hidden-end-consultation');if(!el){console.error('Clarke: hidden-end-consultation not found');return;}if(el.tagName==='BUTTON'){el.click();}else{var b=el.querySelector('button');if(b)b.click();}console.log('Clarke: End Consultation clicked');})()\" style='display:block; width:100%; padding:18px 0; border:none; cursor:pointer; background:linear-gradient(135deg, #D4AF37 0%, #F0D060 100%); color:#1A1A2E; font-family:'Inter',sans-serif; font-weight:700; font-size:16px; letter-spacing:0.5px; transition:all 0.3s ease; box-shadow:0 -4px 16px rgba(212,175,55,0.3);' onmouseover=\"this.style.background='linear-gradient(135deg,#E8C84A,#F5E070)';this.style.boxShadow='0 -4px 24px rgba(212,175,55,0.5)';this.style.transform='translateY(-1px)'\" onmouseout=\"this.style.background='linear-gradient(135deg,#D4AF37,#F0D060)';this.style.boxShadow='0 -4px 16px rgba(212,175,55,0.3)';this.style.transform='translateY(0)'\">End Consultation</button></div>""")
            hidden_end_btn = gr.Button("hidden-end-consultation", visible=True, elem_id="hidden-end-consultation")

        with gr.Column(visible=False) as screen_s4:
            processing_html = gr.HTML(_processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"))
            processing_tick = gr.Timer(value=1.0, active=False)
            hidden_cancel_button = gr.Button("hidden-cancel", visible=True, elem_id="hidden-cancel")

        with gr.Column(visible=False) as screen_s5:
            gr.HTML("<div style='min-height:100vh;background:#F8F6F1;padding:32px 48px;margin:0;'><h2 style='font-family:DM Serif Display,serif;color:#1A1A2E;margin:0 0 16px 0;'>Document Review</h2></div>")
            review_status_badge = gr.HTML(build_status_badge_html("✎ Ready for Review", "#F59E0B"))
            review_fhir_values = gr.HTML("<span style='font-family:JetBrains Mono,monospace;'>FHIR values appear here.</span>")
            section_one_text = gr.Textbox(label="Section 1", lines=5, interactive=True)
            section_two_text = gr.Textbox(label="Section 2", lines=5, interactive=True)
            section_three_text = gr.Textbox(label="Section 3", lines=5, interactive=True)
            section_four_text = gr.Textbox(label="Section 4", lines=5, interactive=True)
            hidden_regenerate_button = gr.Button("hidden-regenerate", visible=True, elem_id="hidden-regenerate")
            gr.HTML(f"<div style='display:flex;gap:12px;'><button onclick=\"{_hidden_click_js('hidden-regenerate', 'Regenerate')}\" class='clarke-btn-secondary'>↻ Regenerate</button></div>")
            gr.HTML("""<div style='position:sticky; bottom:0; left:0; right:0; z-index:100;'><button onclick=\"(function(){var el=document.getElementById('hidden-sign-off');if(!el){console.error('Clarke: hidden-sign-off not found');return;}if(el.tagName==='BUTTON'){el.click();}else{var b=el.querySelector('button');if(b)b.click();}console.log('Clarke: Sign Off & Export clicked');})()\" style='display:block; width:100%; padding:18px 0; border:none; cursor:pointer; background:linear-gradient(135deg, #D4AF37 0%, #F0D060 100%); color:#1A1A2E; font-family:'Inter',sans-serif; font-weight:700; font-size:16px; letter-spacing:0.5px; transition:all 0.3s ease; box-shadow:0 -4px 16px rgba(212,175,55,0.3);' onmouseover=\"this.style.background='linear-gradient(135deg,#E8C84A,#F5E070)';this.style.boxShadow='0 -4px 24px rgba(212,175,55,0.5)';this.style.transform='translateY(-1px)'\" onmouseout=\"this.style.background='linear-gradient(135deg,#D4AF37,#F0D060)';this.style.boxShadow='0 -4px 16px rgba(212,175,55,0.3)';this.style.transform='translateY(0)'\">Sign Off & Export</button></div>""")
            hidden_sign_off_btn = gr.Button("hidden-sign-off", visible=True, elem_id="hidden-sign-off")

        with gr.Column(visible=False) as screen_s6:
            gr.HTML("")
            signed_status_badge = gr.HTML(build_status_badge_html("✓ Signed Off", "#22C55E"))
            signed_letter_html = gr.HTML("")
            copy_to_clipboard_text = gr.Textbox(label="Copy to Clipboard", interactive=False)
            download_text_file = gr.File(label="Download as Text")
            hidden_copy_button = gr.Button("hidden-copy", visible=True, elem_id="hidden-copy")
            hidden_download_button = gr.Button("hidden-download", visible=True, elem_id="hidden-download")
            gr.HTML("""<div style='display:flex;gap:12px;margin-top:24px;justify-content:center;'><button onclick=\"(function(){var letterEl=document.getElementById('signed-letter-text');if(!letterEl){var textboxes=document.querySelectorAll('textarea');var text='';textboxes.forEach(function(t){if(t.value&&t.value.length>50)text=t.value;});if(!text){alert('No letter text found');return;}navigator.clipboard.writeText(text).then(function(){alert('Copied to clipboard!');}).catch(function(){var ta=document.createElement('textarea');ta.value=text.trim();document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);alert('Copied to clipboard!');});return;}navigator.clipboard.writeText(letterEl.innerText).then(function(){alert('Copied to clipboard!');}).catch(function(){var ta=document.createElement('textarea');ta.value=(letterEl.innerText||'').trim();document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);alert('Copied to clipboard!');});})()\" style='background:transparent; color:#1A1A2E; border:2px solid #D4AF37; padding:12px 24px; border-radius:8px; font-family:'Inter',sans-serif; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.3s ease;' onmouseover=\"this.style.background='rgba(212,175,55,0.1)';this.style.boxShadow='0 0 12px rgba(212,175,55,0.3)';this.style.transform='translateY(-2px)'\" onmouseout=\"this.style.background='transparent';this.style.boxShadow='none';this.style.transform='translateY(0)'\">📋 Copy to Clipboard</button><button onclick=\"(function(){var letterEl=document.getElementById('signed-letter-text');var text=letterEl?letterEl.innerText:'';if(!text){var textboxes=document.querySelectorAll('textarea');textboxes.forEach(function(t){if(t.value&&t.value.length>50)text=t.value;});}if(!text){alert('No letter text found');return;}var blob=new Blob([text],{type:'text/plain'});var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='clinic_letter.txt';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(a.href);console.log('Clarke: Letter downloaded');})()\" style='background:transparent; color:#1A1A2E; border:2px solid #D4AF37; padding:12px 24px; border-radius:8px; font-family:'Inter',sans-serif; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.3s ease;' onmouseover=\"this.style.background='rgba(212,175,55,0.1)';this.style.boxShadow='0 0 12px rgba(212,175,55,0.3)';this.style.transform='translateY(-2px)'\" onmouseout=\"this.style.background='transparent';this.style.boxShadow='none';this.style.transform='translateY(0)'\">📄 Download as Text</button></div>""")
            gr.HTML("""<div style='position:sticky; bottom:0; left:0; right:0; z-index:100;'><button onclick=\"(function(){var el=document.getElementById('hidden-next-patient');if(!el){console.error('Clarke: hidden-next-patient not found');return;}if(el.tagName==='BUTTON'){el.click();}else{var b=el.querySelector('button');if(b)b.click();}console.log('Clarke: Next Patient clicked');})()\" style='display:block; width:100%; padding:18px 0; border:none; cursor:pointer; background:linear-gradient(135deg, #D4AF37 0%, #F0D060 100%); color:#1A1A2E; font-family:'Inter',sans-serif; font-weight:700; font-size:16px; letter-spacing:0.5px; transition:all 0.3s ease; box-shadow:0 -4px 16px rgba(212,175,55,0.3);' onmouseover=\"this.style.background='linear-gradient(135deg,#E8C84A,#F5E070)';this.style.boxShadow='0 -4px 24px rgba(212,175,55,0.5)';this.style.transform='translateY(-1px)'\" onmouseout=\"this.style.background='linear-gradient(135deg,#D4AF37,#F0D060)';this.style.boxShadow='0 -4px 16px rgba(212,175,55,0.3)';this.style.transform='translateY(0)'\">Next Patient →</button></div>""")
            hidden_next_patient_btn = gr.Button("hidden-next-patient", visible=True, elem_id="hidden-next-patient")

        with gr.Column(visible=True) as screen_s1:
            dashboard_html = gr.HTML(build_dashboard_html(clinic_payload))
            hidden_patient_buttons: list[gr.Button] = []
            for i in range(5):
                hidden_patient_buttons.append(gr.Button(f"hidden-select-{i}", elem_id=f"hidden-select-{i}", visible=True))

        for i, hidden_btn in enumerate(hidden_patient_buttons):
            hidden_btn.click(
                fn=lambda state, idx=i: _handle_patient_selection(state, idx),
                inputs=[app_state],
                outputs=[app_state, feedback_text, context_screen_html, section_one_text, section_two_text, section_three_text, section_four_text, signed_letter_html, review_fhir_values, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6],
                show_progress="full",
            )

        hidden_back_button.click(_handle_back_to_dashboard, inputs=[app_state], outputs=[app_state, feedback_text, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        hidden_start_button.click(_handle_start_consultation, inputs=[app_state], outputs=[app_state, feedback_text, recording_html, recording_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        recording_tick.tick(_update_recording_timer, inputs=[app_state], outputs=[recording_html], show_progress="hidden")
        hidden_end_btn.click(_start_processing, inputs=[app_state, consultation_audio], outputs=[app_state, feedback_text, processing_html, processing_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="full")
        processing_tick.tick(_poll_processing_progress, inputs=[app_state], outputs=[app_state, feedback_text, processing_html, processing_tick, section_one_text, section_two_text, section_three_text, section_four_text, review_fhir_values, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        hidden_cancel_button.click(_cancel_processing, inputs=[app_state], outputs=[app_state, feedback_text, processing_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")
        hidden_regenerate_button.click(_regenerate_document, inputs=[app_state], outputs=[app_state, feedback_text, processing_html, processing_tick, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="full")
        hidden_sign_off_btn.click(_sign_off_document, inputs=[app_state, section_one_text, section_two_text, section_three_text, section_four_text], outputs=[app_state, feedback_text, signed_letter_html, copy_to_clipboard_text, download_text_file, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="full")
        hidden_copy_button.click(_copy_signed_document, inputs=[app_state], outputs=[app_state, feedback_text, copy_to_clipboard_text], show_progress="hidden")
        hidden_download_button.click(_prepare_signed_download, inputs=[app_state], outputs=[app_state, feedback_text, download_text_file], show_progress="hidden")
        hidden_next_patient_btn.click(_next_patient, inputs=[app_state], outputs=[app_state, feedback_text, section_one_text, section_two_text, section_three_text, section_four_text, signed_letter_html, copy_to_clipboard_text, dashboard_html, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6], show_progress="hidden")

    return demo
