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

CLARKE_HEAD = """
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
@keyframes clarkeGradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes clarkeLogoShimmer {
    0% { filter: brightness(1) drop-shadow(0 0 2px rgba(212,175,55,0.3)); }
    50% { filter: brightness(1.4) drop-shadow(0 0 8px rgba(212,175,55,0.6)); }
    100% { filter: brightness(1) drop-shadow(0 0 2px rgba(212,175,55,0.3)); }
}
.gradio-container, [class*="gradio-container-"] {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 auto !important;
}
footer { display: none !important; }
</style>
<script>
(function() {
    function installClarkeHeadScript() {
    function enforceLayout() {
        var app = document.querySelector('gradio-app');
        if (app) {
            app.style.setProperty('padding', '0', 'important');
            app.style.setProperty('margin', '0', 'important');
            app.style.setProperty('overflow-x', 'hidden', 'important');
        }
        document.querySelectorAll('.gradio-container, [class*="gradio-container-"]').forEach(function(el) {
            el.style.setProperty('max-width', '100%', 'important');
            el.style.setProperty('padding', '0', 'important');
            el.style.setProperty('margin', '0', 'important');
        });
        var f = document.querySelector('footer');
        if (f) f.style.display = 'none';
    }

    enforceLayout();
    [100, 500, 1000, 2000, 5000].forEach(function(ms) {
        setTimeout(enforceLayout, ms);
    });

    new MutationObserver(enforceLayout).observe(document.body, {
        childList: true, subtree: true, attributes: true, attributeFilter: ['style','class']
    });

    setTimeout(function() {
        ['hidden-select-0','hidden-select-1','hidden-select-2','hidden-select-3','hidden-select-4',
         'hidden-start-consultation','hidden-end-consultation','hidden-sign-off','hidden-next-patient',
         'hidden-back','hidden-review-letter'].forEach(function(id) {
            var el = document.getElementById(id);
            if (el) {
                var node = el;
                for (var i = 0; i < 4; i++) {
                    node.style.cssText = 'position:fixed!important;top:-9999px!important;left:-9999px!important;width:1px!important;height:1px!important;opacity:0!important;overflow:hidden!important;';
                    node = node.parentElement;
                    if (!node || node.tagName === 'FORM') break;
                }
            }
        });
        console.log('Clarke: Bridge buttons hidden');
    }, 800);

    console.log('Clarke: Layout enforcer installed via head script');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', installClarkeHeadScript);
    } else {
        installClarkeHeadScript();
    }
})();
</script>
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


def _letter_prefs_persistence_js() -> str:
    """Return an HTML snippet that persists letter preference values via JavaScript."""
    return """<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="(function(){
        if(window.clarkePrefsInitDone)return;
        window.clarkePrefsInitDone=true;
        window.clarkeLetterPrefs={};
        function getInputs(){
            var acc=document.getElementById('clarke-letter-prefs');
            if(!acc)return[];
            return Array.prototype.slice.call(acc.querySelectorAll('input[type=text],textarea'));
        }
        function saveAll(){
            var inputs=getInputs();
            for(var i=0;i<inputs.length;i++){
                window.clarkeLetterPrefs[i]=inputs[i].value;
            }
        }
        function restoreAll(){
            var inputs=getInputs();
            if(inputs.length===0)return;
            var changed=false;
            for(var i=0;i<inputs.length;i++){
                var saved=window.clarkeLetterPrefs[i];
                if(saved!==undefined&&saved!==inputs[i].value){
                    var proto=inputs[i].tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
                    var setter=Object.getOwnPropertyDescriptor(proto,'value');
                    if(setter&&setter.set){setter.set.call(inputs[i],saved);}
                    else{inputs[i].value=saved;}
                    inputs[i].dispatchEvent(new Event('input',{bubbles:true}));
                    inputs[i].dispatchEvent(new Event('change',{bubbles:true}));
                    changed=true;
                }
            }
            if(changed)console.log('Clarke: Restored letter prefs');
        }
        function attachListeners(){
            var inputs=getInputs();
            inputs.forEach(function(inp){
                if(!inp.dataset.clarkeTracked){
                    inp.dataset.clarkeTracked='1';
                    inp.addEventListener('input',function(){saveAll();});
                    inp.addEventListener('change',function(){saveAll();});
                }
            });
        }
        function check(){
            var inputs=getInputs();
            if(inputs.length>0){
                attachListeners();
                if(Object.keys(window.clarkeLetterPrefs).length>0){restoreAll();}
            }
        }
        new MutationObserver(function(){check();}).observe(document.body,{childList:true,subtree:true});
        setInterval(check,2000);
        console.log('Clarke: Letter prefs persistence active');
    })()" style="display:none;position:absolute;width:0;height:0;">"""


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
    prefs = (state or {}).get("letter_prefs", {})
    gp_name = prefs.get("gp_name", "Dr Andrew Wilson").replace("Dr ", "", 1)
    address = prefs.get("gp_address", "Riverside Medical Practice\n14 Harcourt Street\nLondon")
    clinician_display = prefs.get("clinician_name", "Dr Sarah Chen")
    clinician_title = prefs.get("clinician_title", "Consultant, General Practice")
    hospital_name = prefs.get("hospital", "Clarke NHS Trust")
    signoff_phrase = prefs.get("signoff_phrase", "Warm regards")

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

    clinical_issues_text = "\n".join(f"- {item}" for item in problems) if problems else "- None listed"

    letter_text = (
        f"{today}\n\n"
        f"Dr {gp_name}\n"
        f"{address}\n\n"
        f"Dear Dr {gp_name},\n\n"
        f"Re: {patient_name} (DOB: {dob}, NHS: {nhs})\n"
        f"    {address}\n\n"
        f"Thank you for referring / I reviewed {patient_name} in {clinician_title.split(',')[-1].strip() if ',' in clinician_title else clinician_title} Clinic on {today}.\n\n"
        "History of Presenting Complaint\n"
        f"{history}\n\n"
        "Examination\n"
        "The patient was comfortable at rest, haemodynamically stable, and clinically euvolaemic on examination. No acute red-flag findings were identified today.\n\n"
        "Investigations\n"
        f"{investigations}\n\n"
        "Clinical Issues\n"
        f"{clinical_issues_text}\n\n"
        "Current Medications\n"
        f"{medication_line or 'None documented'}\n\n"
        "Assessment\n"
        f"{assessment}\n\n"
        "Plan\n"
        + "\n".join(f"{i + 1}. {line}" for i, line in enumerate(plan_lines))
        + f"\n\nI will review {patient_name} in 8 weeks. Please do not hesitate to contact us if there are any concerns in the interim.\n\n"
        f"{signoff_phrase},\n\n"
        f"{clinician_display}\n"
        f"{clinician_title}\n"
        f"{hospital_name}"
    )

    doc_type = (state or {}).get("doc_type", "Clinic Letter")

    if doc_type == "Ward Round Note":
        now_time = datetime.now().strftime("%H:%M")

        if "Margaret Thompson" in patient_name:
            overnight = "Remained stable overnight. Blood glucose levels ranged 8.4-14.2 mmol/L. No hypoglycaemic episodes. Nursing staff report adequate oral intake."
            current_status = "Alert and oriented. Reports mild fatigue but no chest pain, dyspnoea, or new symptoms. Tolerating diet well."
            exam_findings = "Obs: BP 142/88, HR 78 regular, SpO2 97% RA, Temp 36.8. CVS: HS I+II+0, no peripheral oedema. Resp: Clear bilaterally. Abdo: Soft, non-tender."
            today_plan = [
                "Optimise glycaemic control — consider increasing gliclazide to 80mg BD.",
                "Chase repeat HbA1c and renal profile results from this morning.",
                "Dietitian review requested for structured carbohydrate counselling.",
                "Continue current medications including lisinopril 10mg OD and atorvastatin 40mg ON.",
                "Aim for discharge tomorrow if glucose control improving — arrange diabetes nurse follow-up within 1 week.",
            ]
        else:
            overnight = f"Stable overnight. No acute events reported by nursing staff. Observations within acceptable parameters for {main_problem.lower()}."
            current_status = f"Patient reports feeling stable this morning. Ongoing management of {main_problem.lower()} continues."
            exam_findings = "Obs: Within normal limits. Systems examination unremarkable. No new clinical findings."
            today_plan = [
                "Continue current management plan.",
                "Review outstanding investigation results.",
                "Reassess clinical progress and escalation needs.",
                "Estimated discharge: pending clinical improvement.",
            ]

        clinical_issues_ward = "\n".join(f"- {item}" for item in problems) if problems else "- None listed"

        ward_note_text = (
            f"WARD ROUND NOTE — {today} at {now_time}\n"
            f"{'=' * 50}\n\n"
            f"Patient: {patient_name}\n"
            f"DOB: {dob} | NHS: {nhs}\n"
            f"Ward: General Medical | Bed: 12A\n"
            f"Consultant: {clinician_display}\n\n"
            f"Day {2} of admission | Primary Dx: {main_problem}\n\n"
            "Overnight Events\n"
            f"{overnight}\n\n"
            "Current Status\n"
            f"{current_status}\n\n"
            "Examination Findings\n"
            f"{exam_findings}\n\n"
            "Investigations\n"
            f"{investigations}\n\n"
            "Current Medications\n"
            f"{medication_line or 'As per drug chart'}\n\n"
            "Clinical Issues\n"
            f"{clinical_issues_ward}\n\n"
            "Assessment\n"
            f"{assessment}\n\n"
            "Plan\n"
            + "\n".join(f"{i + 1}. {line}" for i, line in enumerate(today_plan))
            + f"\n\n{clinician_display} | {clinician_title} | {hospital_name}\n"
            f"Documented at {now_time} on {today}"
        )

        sections = [
            {"heading": "Ward Round Note", "content": ward_note_text},
        ]
        return {
            "title": "Ward Round Note",
            "status": "ready_for_review",
            "sections": sections,
            "patient_name": patient_name,
            "nhs_number": nhs,
        }

    sections = [
        {"heading": "NHS Clinic Letter", "content": letter_text},
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

    Combines all sections into section 1 as the full editable letter.
    Sections 2-4 are hidden and returned empty.

    Args:
        letter_sections (list[dict[str, str]]): Ordered letter sections.

    Returns:
        tuple[str, str, str, str]: Combined letter in slot 1, empty slots 2-4.
    """

    combined = "\n\n".join(
        f"{s.get('heading', '')}\n{s.get('content', '').strip()}".strip()
        for s in letter_sections
        if s.get('content', '').strip()
    )
    return (combined, "", "", "")


def _handle_patient_selection(state: dict[str, Any], patient_index: int, clinician_name: str = "Dr Sarah Chen", clinician_title: str = "Consultant, General Practice", hospital: str = "Clarke NHS Trust", department: str = "General Practice Department", gp_name: str = "Dr Andrew Wilson", signoff_phrase: str = "Warm regards", gp_address: str = "Riverside Medical Practice\n14 Harcourt Street\nLondon", doc_type: str = "Clinic Letter"):
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
    updated_state["letter_prefs"] = {
        "clinician_name": clinician_name or "Dr Sarah Chen",
        "clinician_title": clinician_title or "Consultant, General Practice",
        "hospital": hospital or "Clarke NHS Trust",
        "department": department or "General Practice Department",
        "gp_name": gp_name or "Dr Andrew Wilson",
        "gp_address": gp_address or "Riverside Medical Practice\n14 Harcourt Street\nLondon",
        "signoff_phrase": signoff_phrase or "Warm regards",
    }
    updated_state["doc_type"] = doc_type or "Clinic Letter"
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




def _ensure_mock_audio_file(audio_path: str | None, state: dict | None = None) -> str | None:
    """Return audio path, falling back to demo audio files for known patients."""

    if audio_path:
        return audio_path

    # Map patient indices to demo audio files
    DEMO_AUDIO_MAP = {
        0: "data/demo/mrs_thompson.wav",
        1: "data/demo/mr_okafor.wav",
        2: "data/demo/ms_patel.wav",
    }

    patient_index = (state or {}).get("current_patient_index")
    if patient_index is not None and patient_index in DEMO_AUDIO_MAP:
        demo_path = Path(DEMO_AUDIO_MAP[patient_index])
        if demo_path.exists():
            return str(demo_path)

    # Fallback: generate a short silent WAV for patients without demo audio
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
    raw_consultation_id = (updated_state.get("consultation") or {}).get("id")
    consultation_id = str(raw_consultation_id) if raw_consultation_id is not None else ""
    if not consultation_id:
        return updated_state, "Consultation session is missing. Start consultation again.", _processing_screen_html(1, "Finalising transcript…", "MedASR processing audio", "Elapsed: 00:00"), gr.update(active=False), *show_screen("s3")

    resolved_audio_path = _ensure_mock_audio_file(audio_path, state=updated_state)
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
    raw_consultation_id = (updated_state.get("consultation") or {}).get("id")
    consultation_id = str(raw_consultation_id) if raw_consultation_id is not None else ""
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

    signed_letter = section_1.strip() if section_1 and section_1.strip() else "\n\n".join(part.strip() for part in edited_sections if part and part.strip())
    
    updated_state["signed_document_text"] = signed_letter
    selected_index = int(updated_state.get('current_patient_index', 0))
    signed_letters = dict(updated_state.get('signed_letters', {}))
    signed_letters[str(selected_index)] = signed_letter
    updated_state['signed_letters'] = signed_letters
    if "consultation" not in updated_state or not isinstance(updated_state.get("consultation"), dict):
        updated_state["consultation"] = {"id": None, "status": "idle"}
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

def _next_patient(state, p_cn, p_ct, p_ho, p_de, p_gp, p_so, p_ga, p_dt):
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
    refreshed_state['doc_type'] = p_dt or updated_state.get('doc_type', 'Clinic Letter')
    refreshed_state['letter_prefs'] = {
        "clinician_name": p_cn or "Dr Sarah Chen",
        "clinician_title": p_ct or "Consultant, General Practice",
        "hospital": p_ho or "Clarke NHS Trust",
        "department": p_de or "General Practice Department",
        "gp_name": p_gp or "Dr Andrew Wilson",
        "signoff_phrase": p_so or "Warm regards",
        "gp_address": p_ga or "Riverside Medical Practice\n14 Harcourt Street\nLondon",
    }
    return (
        refreshed_state,
        "Ready for next patient. Please select a patient card.",
        "",
        "",
        "",
        "",
        "",
        "",
        dashboard,
        *show_screen("s1"),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
    )


def build_ui() -> gr.Blocks:
    """Build the primary Clarke UI blocks for the dashboard flow.

    Args:
        None: Function reads local static assets and clinic JSON data.

    Returns:
        gr.Blocks: Configured Gradio Blocks application.
    """

    clinic_payload = load_clinic_list()

    with gr.Blocks(theme=clarke_theme, css=Path("frontend/assets/style.css").read_text(encoding="utf-8"), title="Clarke", head=CLARKE_HEAD) as demo:
        app_state = gr.State(initial_consultation_state())
        gr.HTML(build_global_style_block())
        gr.HTML("""<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="(function(){function fix(){var el=document.getElementById('clarke-doc-type');if(!el)return;var p=el.parentElement;while(p&&p!==document.body){p.style.setProperty('background','transparent','important');p.style.setProperty('border','none','important');p.style.setProperty('box-shadow','none','important');p.style.setProperty('padding','0','important');if(p.classList.contains('form')||p.classList.contains('block'))break;p=p.parentElement;}el.style.setProperty('background','rgba(255,255,255,0.6)','important');el.style.setProperty('border','1px solid rgba(212,175,55,0.2)','important');el.style.setProperty('border-radius','12px','important');el.style.setProperty('backdrop-filter','blur(8px)','important');el.style.setProperty('-webkit-backdrop-filter','blur(8px)','important');el.style.setProperty('box-shadow','0 2px 8px rgba(0,0,0,0.03)','important');el.style.setProperty('overflow','hidden','important');el.style.setProperty('padding','0','important');var kids=el.querySelectorAll('div,fieldset');for(var i=0;i<kids.length;i++){kids[i].style.setProperty('background','transparent','important');kids[i].style.setProperty('border-color','transparent','important');kids[i].style.setProperty('box-shadow','none','important');}var wrap=el.querySelector('.wrap');if(wrap){wrap.style.setProperty('padding','4px 20px 16px 20px','important');wrap.style.setProperty('border-top','1px solid rgba(212,175,55,0.12)','important');wrap.style.setProperty('gap','12px','important');wrap.style.setProperty('background','transparent','important');}var title=el.querySelector('span[data-testid=block-info]');if(title){title.style.setProperty('font-family','DM Serif Display,serif','important');title.style.setProperty('font-size','16px','important');title.style.setProperty('color','#D4AF37','important');title.style.setProperty('padding','14px 20px 8px 20px','important');title.style.setProperty('display','block','important');}var labels=el.querySelectorAll('label');for(var j=0;j<labels.length;j++){labels[j].style.setProperty('font-family','DM Serif Display,serif','important');labels[j].style.setProperty('font-size','14px','important');labels[j].style.setProperty('border','1px solid rgba(212,175,55,0.25)','important');labels[j].style.setProperty('border-radius','8px','important');labels[j].style.setProperty('padding','10px 20px','important');labels[j].style.setProperty('cursor','pointer','important');labels[j].style.setProperty('background','rgba(255,255,255,0.6)','important');labels[j].style.setProperty('color','#555','important');}var radios=el.querySelectorAll('input[type=radio]');for(var k=0;k<radios.length;k++){radios[k].style.setProperty('accent-color','#D4AF37','important');}}fix();[100,300,600,1200,2500].forEach(function(t){setTimeout(fix,t);});new MutationObserver(function(){fix();}).observe(document.documentElement,{childList:true,subtree:true});})()" style="display:none;position:absolute;width:0;height:0;">""")
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
            gr.HTML("<h2 style='font-family:DM Serif Display,serif;color:#1A1A2E;margin:0;padding:8px 0 0 0;'>Document Review</h2>")
            review_status_badge = gr.HTML(build_status_badge_html("✎ Ready for Review", "#F59E0B"))
            review_fhir_values = gr.HTML("<span style='font-family:JetBrains Mono,monospace;'>FHIR values appear here.</span>")
            section_one_text = gr.Textbox(label="Document", lines=20, interactive=True)
            section_two_text = gr.Textbox(label="Section 2", lines=5, interactive=True, visible=False)
            section_three_text = gr.Textbox(label="Section 3", lines=5, interactive=True, visible=False)
            section_four_text = gr.Textbox(label="Section 4", lines=5, interactive=True, visible=False)
            hidden_regenerate_button = gr.Button("hidden-regenerate", visible=True, elem_id="hidden-regenerate")
            gr.HTML("<div></div>")
            gr.HTML("""<div style='position:sticky; bottom:0; left:0; right:0; z-index:100;'><button onclick=\"(function(){var el=document.getElementById('hidden-sign-off');if(!el){console.error('Clarke: hidden-sign-off not found');return;}if(el.tagName==='BUTTON'){el.click();}else{var b=el.querySelector('button');if(b)b.click();}console.log('Clarke: Sign Off & Export clicked');})()\" style='display:block; width:100%; padding:18px 0; border:none; cursor:pointer; background:linear-gradient(135deg, #D4AF37 0%, #F0D060 100%); color:#1A1A2E; font-family:'Inter',sans-serif; font-weight:700; font-size:16px; letter-spacing:0.5px; transition:all 0.3s ease; box-shadow:0 -4px 16px rgba(212,175,55,0.3);' onmouseover=\"this.style.background='linear-gradient(135deg,#E8C84A,#F5E070)';this.style.boxShadow='0 -4px 24px rgba(212,175,55,0.5)';this.style.transform='translateY(-1px)'\" onmouseout=\"this.style.background='linear-gradient(135deg,#D4AF37,#F0D060)';this.style.boxShadow='0 -4px 16px rgba(212,175,55,0.3)';this.style.transform='translateY(0)'\">Sign Off & Export</button></div>""")
            hidden_sign_off_btn = gr.Button("hidden-sign-off", visible=True, elem_id="hidden-sign-off")

        with gr.Column(visible=False) as screen_s6:
            gr.HTML("")
            signed_status_badge = gr.HTML(build_status_badge_html("✓ Signed Off", "#22C55E"))
            signed_letter_html = gr.HTML("")
            copy_to_clipboard_text = gr.Textbox(label="Copy to Clipboard", interactive=False, visible=False)
            download_text_file = gr.File(label="Download as Text", visible=False)
            hidden_copy_button = gr.Button("hidden-copy", visible=True, elem_id="hidden-copy")
            hidden_download_button = gr.Button("hidden-download", visible=True, elem_id="hidden-download")
            gr.HTML("""<div style='display:flex;gap:12px;margin-top:24px;justify-content:center;'><button onclick=\"(function(){var el=document.getElementById('signed-letter-text');var text='';if(el){text=el.innerText||el.textContent;}if(!text){document.querySelectorAll('textarea').forEach(function(t){if(t.value&&t.value.length>50)text=t.value;});}if(!text){alert('No letter text found');return;}try{navigator.clipboard.writeText(text.trim()).then(function(){alert('Copied to clipboard!');});}catch(e){var ta=document.createElement('textarea');ta.value=text.trim();document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);alert('Copied to clipboard!');}})()\" style='background:transparent; color:#1A1A2E; border:2px solid #D4AF37; padding:12px 24px; border-radius:8px; font-family:Inter,sans-serif; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.3s ease;' onmouseover=\"this.style.background='rgba(212,175,55,0.1)';this.style.boxShadow='0 0 12px rgba(212,175,55,0.3)';this.style.transform='translateY(-2px)'\" onmouseout=\"this.style.background='transparent';this.style.boxShadow='none';this.style.transform='translateY(0)'\">📋 Copy to Clipboard</button><button onclick="clarkePrintPDF()" style='background:transparent; color:#1A1A2E; border:2px solid #D4AF37; padding:12px 24px; border-radius:8px; font-family:Inter,sans-serif; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.3s ease;' onmouseover="this.style.background='rgba(212,175,55,0.1)';this.style.boxShadow='0 0 12px rgba(212,175,55,0.3)';this.style.transform='translateY(-2px)'" onmouseout="this.style.background='transparent';this.style.boxShadow='none';this.style.transform='translateY(0)'">📑 Download as PDF</button><button onclick=\"(function(){console.log('Clarke: Download clicked');var el=document.getElementById('signed-letter-text');var text='';if(el){text=el.innerText||el.textContent;}if(!text){document.querySelectorAll('textarea').forEach(function(t){if(t.value&&t.value.length>50)text=t.value;});}if(!text){alert('No letter text found');return;}var a=document.createElement('a');a.href='data:text/plain;charset=utf-8,'+encodeURIComponent(text.trim());a.download='clinic_letter.txt';a.style.display='none';document.body.appendChild(a);a.click();document.body.removeChild(a);console.log('Clarke: Download complete via data URI');})()\" style='background:transparent; color:#1A1A2E; border:2px solid #D4AF37; padding:12px 24px; border-radius:8px; font-family:Inter,sans-serif; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.3s ease;' onmouseover=\"this.style.background='rgba(212,175,55,0.1)';this.style.boxShadow='0 0 12px rgba(212,175,55,0.3)';this.style.transform='translateY(-2px)'\" onmouseout=\"this.style.background='transparent';this.style.boxShadow='none';this.style.transform='translateY(0)'\">📄 Download as Text</button></div>""")
            gr.HTML("""<div style='position:sticky; bottom:0; left:0; right:0; z-index:100;'><button onclick=\"(function(){var el=document.getElementById('hidden-next-patient');if(!el){console.error('Clarke: hidden-next-patient not found');return;}if(el.tagName==='BUTTON'){el.click();}else{var b=el.querySelector('button');if(b)b.click();}console.log('Clarke: Next Patient clicked');})()\" style='display:block; width:100%; padding:18px 0; border:none; cursor:pointer; background:linear-gradient(135deg, #D4AF37 0%, #F0D060 100%); color:#1A1A2E; font-family:'Inter',sans-serif; font-weight:700; font-size:16px; letter-spacing:0.5px; transition:all 0.3s ease; box-shadow:0 -4px 16px rgba(212,175,55,0.3);' onmouseover=\"this.style.background='linear-gradient(135deg,#E8C84A,#F5E070)';this.style.boxShadow='0 -4px 24px rgba(212,175,55,0.5)';this.style.transform='translateY(-1px)'\" onmouseout=\"this.style.background='linear-gradient(135deg,#D4AF37,#F0D060)';this.style.boxShadow='0 -4px 16px rgba(212,175,55,0.3)';this.style.transform='translateY(0)'\">Next Patient →</button></div>""")
            hidden_next_patient_btn = gr.Button("hidden-next-patient", visible=True, elem_id="hidden-next-patient")

        with gr.Column(visible=True) as screen_s1:
            dashboard_html = gr.HTML(build_dashboard_html(clinic_payload))
            doc_type_radio = gr.Radio(
                choices=["Clinic Letter", "Ward Round Note"],
                value="Clinic Letter",
                label="📋  Document Type",
                interactive=True,
                elem_id="clarke-doc-type",
            )
            with gr.Accordion("⚙  Letter Preferences", open=False, elem_id="clarke-letter-prefs"):
                gr.HTML("<p style='font-family:Inter,sans-serif;font-size:13px;color:#888;margin:0 0 12px 0;font-style:italic;'>Customise the generated clinic letter template. Changes persist for all patients in this clinic list.</p>")
                with gr.Row():
                    pref_clinician_name = gr.Textbox(label="Clinician Name", value="Dr Sarah Chen", interactive=True, scale=1)
                    pref_clinician_title = gr.Textbox(label="Title / Role", value="Consultant, General Practice", interactive=True, scale=1)
                with gr.Row():
                    pref_hospital = gr.Textbox(label="Hospital / Trust", value="Clarke NHS Trust", interactive=True, scale=1)
                    pref_department = gr.Textbox(label="Department", value="General Practice Department", interactive=True, scale=1)
                with gr.Row():
                    pref_gp_name = gr.Textbox(label="Addressee Name", value="Dr Andrew Wilson", interactive=True, scale=1)
                    pref_signoff = gr.Textbox(label="Sign-off Phrase", value="Warm regards", interactive=True, scale=1)
                pref_gp_address = gr.Textbox(label="Addressee Address", value="Riverside Medical Practice\n14 Harcourt Street\nLondon", lines=3, interactive=True)
            gr.HTML(_letter_prefs_persistence_js())
            hidden_patient_buttons: list[gr.Button] = []
            for i in range(5):
                hidden_patient_buttons.append(gr.Button(f"hidden-select-{i}", elem_id=f"hidden-select-{i}", visible=True))

        for i, hidden_btn in enumerate(hidden_patient_buttons):
            hidden_btn.click(
                fn=lambda state, cn, ct, ho, de, gp, so, ga, dt, idx=i: _handle_patient_selection(state, idx, cn, ct, ho, de, gp, so, ga, dt),
                inputs=[app_state, pref_clinician_name, pref_clinician_title, pref_hospital, pref_department, pref_gp_name, pref_signoff, pref_gp_address, doc_type_radio],
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
        hidden_next_patient_btn.click(_next_patient, inputs=[app_state, pref_clinician_name, pref_clinician_title, pref_hospital, pref_department, pref_gp_name, pref_signoff, pref_gp_address, doc_type_radio], outputs=[app_state, feedback_text, section_one_text, section_two_text, section_three_text, section_four_text, signed_letter_html, copy_to_clipboard_text, dashboard_html, screen_s1, screen_s2, screen_s3, screen_s4, screen_s5, screen_s6, pref_clinician_name, pref_clinician_title, pref_hospital, pref_department, pref_gp_name, pref_signoff, pref_gp_address], show_progress="hidden")

    return demo
