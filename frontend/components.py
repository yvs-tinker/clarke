"""HTML builders for Clarke frontend screens."""

from __future__ import annotations

from html import escape
from typing import Any


def _open_patient_click_js(index: int) -> str:
    """Return debug-friendly JS snippet for dashboard patient button clicks.

    Args:
        index (int): Dashboard patient-card index.

    Returns:
        str: Inline JS IIFE for HTML onclick attributes.
    """

    return (
        "(function(){"
        f"var el=document.getElementById('hidden-select-{index}');"
        "if(!el){return;}"
        "if(el.tagName==='BUTTON'){el.click();}else{"
        "var btn=el.querySelector('button');"
        "if(btn){btn.click();}"
        "}"
        "})()"
    )


def build_global_style_block() -> str:
    """Return the global CSS block injected via gr.HTML.

    Args:
        None: This function has no runtime inputs.

    Returns:
        str: Complete style tag with animation keyframes and resets.
    """

    return """
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
  @keyframes clarkeGradientFlow {
    0% { background-position: 50% 0%; }
    25% { background-position: 52% 2%; }
    50% { background-position: 48% 4%; }
    75% { background-position: 51% 1%; }
    100% { background-position: 50% 0%; }
  }
  @keyframes btnShine {0% { left: -100%; }50% { left: 100%; }100% { left: 100%; }}
  @keyframes fadeSlideIn {0% { opacity: 0; transform: translateY(20px); }100% { opacity: 1; transform: translateY(0); }}
  @keyframes recordPulse {0%, 100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.6); }50% { box-shadow: 0 0 0 24px rgba(212, 175, 55, 0); }}
  @keyframes progressSpin {0% { transform: rotate(0deg); }100% { transform: rotate(360deg); }}
  @keyframes progressGlow {0%, 100% { opacity: 0.6; }50% { opacity: 1; }}

  html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: hidden !important;
    background: #E8E4DD !important;
  }
  .gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
  }
  .gradio-container > .main,
  .gradio-container > .main > .wrap,
  .gradio-container .contain {
    max-width: 100% !important;
    padding: 0 !important;
    gap: 0 !important;
    margin: 0 !important;
  }
  #component-0 {
    max-width: 100% !important;
    padding: 0 !important;
    gap: 0 !important;
    margin: 0 !important;
  }
  footer { display: none !important; }
  .gradio-column { padding: 0 !important; gap: 0 !important; }

  #hidden-select-0, #hidden-select-1, #hidden-select-2, #hidden-select-3, #hidden-select-4,
  #hidden-start-consultation, #hidden-back, #hidden-cancel, #hidden-regenerate, #hidden-copy, #hidden-download {
    display: block !important;
    position: fixed !important;
    top: -9999px !important;
    left: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
  }

  .patient-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
    position: relative !important;
    overflow: hidden !important;
  }
  .patient-card:hover {
    transform: translateY(-6px) scale(1.015) !important;
    box-shadow: 0 12px 32px rgba(212, 175, 55, 0.25), 0 4px 12px rgba(0,0,0,0.1) !important;
    border-color: #D4AF37 !important;
  }
  .patient-card:active { transform: translateY(-2px) scale(1.005) !important; }
  .patient-card::after {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: -100% !important;
    width: 100% !important;
    height: 100% !important;
    background: linear-gradient(90deg, transparent, rgba(212,175,55,0.1), transparent) !important;
    transition: left 0.6s ease !important;
    pointer-events: none !important;
    border-radius: inherit !important;
  }
  .patient-card:hover::after { left: 100% !important; }

  .clarke-btn-gold {
    background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%) !important;
    color: #1A1A2E !important;
    border: none !important;
    padding: 12px 28px !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3) !important;
  }
  .clarke-btn-gold:hover {
    background: linear-gradient(135deg, #E8C84A 0%, #F5E070 100%) !important;
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.5), 0 4px 16px rgba(212, 175, 55, 0.3) !important;
    transform: translateY(-2px) !important;
  }
  .clarke-btn-gold:active {
    transform: translateY(0) !important;
    box-shadow: 0 0 12px rgba(212, 175, 55, 0.6) !important;
  }

  .clarke-btn-secondary {
    background: transparent !important;
    color: #1A1A2E !important;
    border: 2px solid #D4AF37 !important;
    padding: 10px 24px !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
  }
  .clarke-btn-secondary:hover {
    background: rgba(212, 175, 55, 0.1) !important;
    box-shadow: 0 0 12px rgba(212, 175, 55, 0.3) !important;
    transform: translateY(-1px) !important;
  }

  #end-consultation-btn button,
  #sign-off-btn button,
  #next-patient-btn button {
    background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%) !important;
    color: #1A1A2E !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3) !important;
  }
  #end-consultation-btn button:hover,
  #sign-off-btn button:hover,
  #next-patient-btn button:hover {
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.5) !important;
    transform: translateY(-2px) !important;
  }

  #clarke-app-wrapper {
    background-size: 100% 200% !important;
    animation: clarkeGradientFlow 12s ease-in-out infinite !important;
  }

  #clarke-audio-input, [data-testid="audio"] {
    position: fixed !important;
    top: -9999px !important;
    left: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    overflow: hidden !important;
  }
</style>
"""


def build_dashboard_html(clinic_payload: dict[str, Any]) -> str:
    """Render the S1 dashboard markup with top gradient and white card area.

    Args:
        clinic_payload (dict[str, Any]): Clinic roster and clinician metadata.

    Returns:
        str: Complete HTML markup for the dashboard screen.
    """

    clinician = clinic_payload.get("clinician", {})
    cards: list[str] = []
    for index, patient in enumerate(clinic_payload.get("patients", [])):
        click_js = _open_patient_click_js(index)
        cards.append(
            f"""
<div class="patient-card" style="background:rgba(255,255,255,0.95);border:1px solid rgba(212,175,55,0.12);border-radius:16px;padding:24px 28px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.04);animation:fadeSlideIn 0.5s ease forwards;animation-delay:{index * 0.1}s;opacity:0;">
  <div style="position:absolute;left:0;top:0;width:3px;height:100%;background:linear-gradient(180deg,#D4AF37,#F0D060);"></div>
  <div style="display:flex;justify-content:space-between;align-items:center;gap:16px;">
    <div>
      <div style="font-family:'Inter',sans-serif;font-size:12px;font-weight:600;color:#D4AF37;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">{escape(str(patient.get('time', '--:--')))}</div>
      <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#1A1A2E;margin-bottom:4px;">{escape(str(patient.get('name', 'Unknown patient')))}</div>
      <div style="font-family:'Inter',sans-serif;font-size:14px;color:#555;margin-bottom:2px;">{escape(str(patient.get('age', '')))} · {escape(str(patient.get('sex', '')))}</div>
      <div style="font-family:'Inter',sans-serif;font-size:14px;color:#555;font-style:italic;">{escape(str(patient.get('summary', '')))}</div>
    </div>
    <button class="clarke-btn-gold" onclick="{click_js}">Open Patient</button>
  </div>
</div>
"""
        )

    return f"""
<div id="clarke-app-wrapper" style="min-height:100vh;margin:0;padding:0;background:linear-gradient(180deg,#0A0E1A 0%,#1E3A8A 8%,#6B2040 18%,#C4522A 28%,#D4AF37 38%,#E8C84A 48%,#F0E0A0 60%,#F8F6F1 75%,#F8F6F1 100%);">
  <div style="padding:32px 48px 24px 48px;">
    <div style="display:flex;align-items:center;margin-bottom:20px;">
      <span style="font-family:'DM Serif Display',serif;font-size:36px;color:#D4AF37;">Clarke</span>
    </div>
    <div style="padding:14px 22px;background:rgba(255,255,255,0.12);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.18);border-radius:12px;border-left:4px solid #D4AF37;">
      <span style="font-family:'DM Serif Display',serif;font-size:20px;color:#F8F6F1;">{escape(str(clinician.get('name', 'Dr. Sarah Chen')))}</span>
      <span style="font-family:'Inter',sans-serif;font-size:14px;color:#F8F6F1;margin-left:12px;">{escape(str(clinician.get('specialty', 'General Practice')))} — {escape(str(clinic_payload.get('date', '13 February 2026')))}</span>
    </div>
  </div>
  <div id="clarke-content-area" style="background:#F8F6F1;margin:0;padding:32px 48px;min-height:70vh;">
    {''.join(cards)}
  </div>
</div>
"""


def build_status_badge_html(label: str, color: str) -> str:
    """Build a rounded status badge.

    Args:
        label (str): Badge text.
        color (str): Accent color hex.

    Returns:
        str: Badge HTML markup.
    """

    return f"<div style='display:inline-flex;align-items:center;gap:6px;padding:6px 16px;border-radius:20px;background:color-mix(in oklab, {color} 12%, white);border:1px solid color-mix(in oklab, {color} 24%, white);font-family:Inter,sans-serif;font-size:13px;font-weight:600;color:{color};'>{escape(label)}</div>"


class _RenderedFragment:
    """Lightweight rendered fragment container for legacy test compatibility."""

    def __init__(self, value: str) -> None:
        """Store rendered HTML fragment value."""

        self.value = value


def build_patient_card(patient: dict[str, Any]) -> _RenderedFragment:
    """Build a legacy patient card fragment for tests and compatibility helpers."""

    markup = f"<div class='patient-card'><strong>{escape(str(patient.get('name', 'Unknown patient')))}</strong></div>"
    return _RenderedFragment(markup)


def build_status_badge(status: str) -> _RenderedFragment:
    """Build a legacy status badge fragment for tests and compatibility helpers."""

    css_class = "clarke-badge-review" if status == "ready" else "clarke-badge"
    return _RenderedFragment(f"<span class='{css_class}'>{escape(status)}</span>")
