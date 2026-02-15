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
        f"console.log('Clarke: Open Patient button clicked for index {index}');"
        f"var el=document.getElementById('hidden-select-{index}');"
        "console.log('Clarke: Found element:', el);"
        "if(!el){"
        f"console.error('Clarke: Element #hidden-select-{index} not found in DOM');"
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
        f"console.error('Clarke: No clickable button found for #hidden-select-{index}');"
        "}"
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
  @keyframes gradientFlow {0% { background-position: 50% 0%; }25% { background-position: 50% 100%; }50% { background-position: 50% 50%; }75% { background-position: 100% 50%; }100% { background-position: 50% 0%; }}
  @keyframes btnShine {0% { left: -100%; }50% { left: 100%; }100% { left: 100%; }}
  @keyframes btnGlow {0% { box-shadow: 0 0 5px rgba(212, 175, 55, 0.3); }50% { box-shadow: 0 0 25px rgba(212, 175, 55, 0.6), 0 0 50px rgba(212, 175, 55, 0.2); }100% { box-shadow: 0 0 5px rgba(212, 175, 55, 0.3); }}
  @keyframes fadeSlideIn {0% { opacity: 0; transform: translateY(20px); }100% { opacity: 1; transform: translateY(0); }}
  @keyframes revealUp {0% { opacity: 0; transform: translateY(30px); }100% { opacity: 1; transform: translateY(0); }}
  @keyframes recordPulse {0%, 100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.6); }50% { box-shadow: 0 0 0 24px rgba(212, 175, 55, 0); }}
  @keyframes progressSpin {0% { transform: rotate(0deg); }100% { transform: rotate(360deg); }}
  @keyframes progressGlow {0%, 100% { opacity: 0.6; }50% { opacity: 1; }}
  @keyframes cardShimmer {0% { left: -100%; }60% { left: 150%; }100% { left: 150%; }}

  html, body { margin: 0 !important; padding: 0 !important; width: 100%; min-height: 100%; }
  .gradio-container {
    background: transparent !important;
    max-width: 100% !important;
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  .gradio-container > .main { padding: 0 !important; gap: 0 !important; }
  .gradio-container > div { padding: 0 !important; margin: 0 !important; gap: 0 !important; }
  .gradio-container .gr-block,.gradio-container .gr-box,.gradio-container .gr-panel,.gradio-container .gr-padded,.gradio-container .block,.gradio-container .panel,.gradio-container .wrap {background: transparent !important;border: none !important;box-shadow: none !important;}
  footer { display: none !important; }
  * {cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22'%3E%3Ccircle cx='11' cy='11' r='4' fill='%23D4AF37' opacity='0.9'/%3E%3Ccircle cx='11' cy='11' r='10' fill='none' stroke='%23D4AF37' stroke-width='1.5' opacity='0.3'/%3E%3C/svg%3E") 11 11, auto;}
  button, a, [role="button"] {cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22'%3E%3Ccircle cx='11' cy='11' r='5' fill='%23D4AF37' opacity='1'/%3E%3Ccircle cx='11' cy='11' r='10' fill='none' stroke='%23D4AF37' stroke-width='2' opacity='0.5'/%3E%3C/svg%3E") 11 11, pointer;}
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
        card = f"""
<div class="patient-card" style="
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(212, 175, 55, 0.12);
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  animation: fadeSlideIn 0.5s ease forwards;
  animation-delay: {index * 0.1}s;
  opacity: 0;
">
  <div style="position: absolute; left: 0; top: 0; width: 3px; height: 100%; background: linear-gradient(180deg, #D4AF37, #F0D060); border-radius: 2px;"></div>
  <div style="display: flex; justify-content: space-between; align-items: center; gap: 16px;">
    <div>
      <div style="font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; color: #D4AF37; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 6px;">{escape(str(patient.get('time', '--:--')))}</div>
      <div style="font-family: 'DM Serif Display', serif; font-size: 20px; color: #1A1A2E; margin-bottom: 4px;">{escape(str(patient.get('name', 'Unknown patient')))}</div>
      <div style="font-family: 'Inter', sans-serif; font-size: 14px; color: #64748B; margin-bottom: 2px;">{escape(str(patient.get('age', '')))} · {escape(str(patient.get('sex', '')))}</div>
      <div style="font-family: 'Inter', sans-serif; font-size: 14px; color: #94A3B8; font-style: italic;">{escape(str(patient.get('summary', '')))}</div>
    </div>
    <button class="open-patient-btn"
      style="
        background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%);
        color: #0A0E1A;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        padding: 10px 24px;
        border: none;
        border-radius: 10px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
      "
      onclick="{click_js}"
    >
      Open Patient
      <div style="position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0) 100%); animation: btnShine 3s ease-in-out infinite;"></div>
    </button>
  </div>
</div>
"""
        cards.append(card)

    return f"""
<style>
    .gradio-container {{
        max-width: 100% !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        background: transparent !important;
    }}
    .gradio-container > .main {{
        max-width: 100% !important;
        padding: 0 !important;
        gap: 0 !important;
    }}
    .gradio-container > .main > .wrap {{
        max-width: 100% !important;
        padding: 0 !important;
        gap: 0 !important;
    }}
    #component-0 {{
        max-width: 100% !important;
        padding: 0 !important;
        gap: 0 !important;
    }}
    body {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    footer {{
        display: none !important;
    }}
</style>
<div id="clarke-app-wrapper" style="min-height:100vh; background: linear-gradient(180deg, #0A0E1A 0%, #1E3A8A 12%, #6B2040 25%, #C4522A 38%, #D4AF37 48%, #E8C84A 55%, #F0E0A0 65%, #F8F6F1 78%, #F8F6F1 100%); background-attachment:fixed; padding:0; margin:0; position: relative; overflow: hidden;">
  <div style="position: relative; padding: 28px 40px 60px 40px; background: linear-gradient(170deg, #04070F 0%, #0A0E1A 12%, #132A78 26%, #530E0E 36%, #B91C1C 44%, #F97316 52%, #F8FAFC 62%, #93C5FD 72%, #1E3A8A 84%, #0A0E1A 100%); background-size: 100% 300%; animation: gradientFlow 12s ease-in-out infinite;">
    <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 100px; background: linear-gradient(to bottom, transparent, #F8F6F1); pointer-events: none;"></div>
    <div style="display: flex; align-items: center; margin-bottom: 20px; position: relative; z-index: 2;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 52" style="width: 44px; height: 48px; margin-right: 14px; filter: drop-shadow(0 0 8px rgba(212, 175, 55, 0.4));">
        <defs>
          <linearGradient id="goldFill" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#F0D060"/>
            <stop offset="40%" stop-color="#D4AF37"/>
            <stop offset="100%" stop-color="#B8860B"/>
          </linearGradient>
        </defs>
        <path d="M24 2 L46 16 L46 38 L24 50 L2 38 L2 16 Z" fill="url(#goldFill)" stroke="#FDE68A" stroke-width="2"/>
      </svg>
      <span style="font-family: 'DM Serif Display', serif; font-size: 36px; color: #D4AF37; letter-spacing: -0.01em; text-shadow: 0 0 20px rgba(212, 175, 55, 0.3);">Clarke</span>
    </div>
    <div style="padding: 14px 22px; background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; border-left: 4px solid #D4AF37; position: relative; z-index: 2;">
      <span style="font-family: 'DM Serif Display', serif; font-size: 20px; color: #F8FAFC;">{escape(str(clinician.get('name', 'Dr. Sarah Chen')))}</span>
      <span style="font-family: 'Inter', sans-serif; font-size: 14px; color: #94A3B8; margin-left: 12px;">{escape(str(clinician.get('specialty', 'General Practice')))} — {escape(str(clinic_payload.get('date', '13 February 2026')))}</span>
    </div>
  </div>
  <div id="clarke-content-area" style="background:#F8F6F1; border-radius:0 0 16px 16px; margin:0 24px 24px 24px; padding:32px 24px; box-shadow:0 4px 24px rgba(0,0,0,0.08); min-height:60vh; position:relative; z-index:1;">
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
