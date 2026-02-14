"""HTML builders for Clarke frontend screens."""

from __future__ import annotations

from html import escape
from typing import Any


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
  @keyframes waveRipple {0% { transform: translateY(0) scaleY(1); }50% { transform: translateY(-8px) scaleY(1.02); }100% { transform: translateY(0) scaleY(1); }}
  @keyframes btnShine {0% { left: -100%; }50% { left: 100%; }100% { left: 100%; }}
  @keyframes btnGlow {0% { box-shadow: 0 0 5px rgba(212, 175, 55, 0.3); }50% { box-shadow: 0 0 25px rgba(212, 175, 55, 0.6), 0 0 50px rgba(212, 175, 55, 0.2); }100% { box-shadow: 0 0 5px rgba(212, 175, 55, 0.3); }}
  @keyframes fadeSlideIn {0% { opacity: 0; transform: translateY(20px); }100% { opacity: 1; transform: translateY(0); }}
  @keyframes fadeIn {0% { opacity: 0; }100% { opacity: 1; }}
  @keyframes revealUp {0% { opacity: 0; transform: translateY(30px); }100% { opacity: 1; transform: translateY(0); }}
  @keyframes recordPulse {0%, 100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.6); }50% { box-shadow: 0 0 0 24px rgba(212, 175, 55, 0); }}
  @keyframes progressSpin {0% { transform: rotate(0deg); }100% { transform: rotate(360deg); }}
  @keyframes progressGlow {0%, 100% { opacity: 0.6; }50% { opacity: 1; }}
  @keyframes shimmer {0% { background-position: -200% 0; }100% { background-position: 200% 0; }}
  @keyframes cardShimmer {0% { left: -100%; }60% { left: 150%; }100% { left: 150%; }}
  .gradio-container {background: transparent !important;max-width: 100% !important;padding: 0 !important;}
  .gradio-container .gr-block,.gradio-container .gr-box,.gradio-container .gr-panel,.gradio-container .gr-padded,.gradio-container .block,.gradio-container .panel,.gradio-container .wrap {background: transparent !important;border: none !important;box-shadow: none !important;}
  footer { display: none !important; }
  * {cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22'%3E%3Ccircle cx='11' cy='11' r='4' fill='%23D4AF37' opacity='0.9'/%3E%3Ccircle cx='11' cy='11' r='10' fill='none' stroke='%23D4AF37' stroke-width='1.5' opacity='0.3'/%3E%3C/svg%3E") 11 11, auto;}
  button, a, [role="button"] {cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22'%3E%3Ccircle cx='11' cy='11' r='5' fill='%23D4AF37' opacity='1'/%3E%3Ccircle cx='11' cy='11' r='10' fill='none' stroke='%23D4AF37' stroke-width='2' opacity='0.5'/%3E%3C/svg%3E") 11 11, pointer;}
  ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); } ::-webkit-scrollbar-thumb { background: rgba(212, 175, 55, 0.4); border-radius: 3px; }
  * { scrollbar-width: thin; scrollbar-color: rgba(212, 175, 55, 0.4) transparent; }
  .gr-audio, audio {border-radius: 12px !important;border: 1px solid rgba(212, 175, 55, 0.3) !important;}
  textarea, .gr-textbox textarea {font-family: 'Inter', sans-serif !important;font-size: 16px !important;line-height: 1.7 !important;background: rgba(255, 255, 255, 0.95) !important;border: 1px solid rgba(212, 175, 55, 0.3) !important;border-radius: 8px !important;padding: 16px !important;}
</style>
"""


def build_dashboard_html(clinic_payload: dict[str, Any]) -> str:
    """Render the S1 dashboard markup with animated gradient and patient cards.

    Args:
        clinic_payload (dict[str, Any]): Clinic roster and clinician metadata.

    Returns:
        str: Complete HTML markup for the dashboard screen.
    """

    clinician = clinic_payload.get("clinician", {})
    cards: list[str] = []
    for index, patient in enumerate(clinic_payload.get("patients", [])):
        patient_id = escape(str(patient.get("id", "")))
        card = f"""
<div style="background: rgba(255, 255, 255, 0.07);backdrop-filter: blur(16px);-webkit-backdrop-filter: blur(16px);border: 1px solid rgba(255, 255, 255, 0.1);border-radius: 16px;padding: 24px 28px;margin: 0 40px 16px 40px;position: relative;overflow: hidden;transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);animation: fadeSlideIn 0.5s ease forwards;animation-delay: {index * 0.1}s;opacity: 0;" onmouseover="this.style.background='rgba(255,255,255,0.12)'; this.style.borderColor='rgba(212,175,55,0.4)'; this.style.transform='translateY(-3px)'; this.style.boxShadow='0 12px 40px rgba(0,0,0,0.3), 0 0 20px rgba(212,175,55,0.1)';" onmouseout="this.style.background='rgba(255,255,255,0.07)'; this.style.borderColor='rgba(255,255,255,0.1)'; this.style.transform='translateY(0)'; this.style.boxShadow='none';">
  <div style="position:absolute;left:0;top:0;width:3px;height:100%;background:linear-gradient(180deg,#D4AF37,#F0D060);opacity:0.6;"></div>
  <div style="position:absolute;top:0;left:-100%;width:50%;height:100%;background:linear-gradient(90deg,rgba(255,255,255,0) 0%, rgba(255,255,255,0.04) 50%, rgba(255,255,255,0) 100%);animation: cardShimmer 8s ease-in-out infinite;"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div style="font-family:Inter,sans-serif;font-size:12px;font-weight:600;color:#D4AF37;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">{escape(str(patient.get('time', '--:--')))}</div>
      <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#F8FAFC;margin-bottom:4px;">{escape(str(patient.get('name', 'Unknown patient')))}</div>
      <div style="font-family:Inter,sans-serif;font-size:14px;color:#94A3B8;margin-bottom:2px;">{escape(str(patient.get('age', '')))} · {escape(str(patient.get('sex', '')))}</div>
      <div style="font-family:Inter,sans-serif;font-size:14px;color:#64748B;font-style:italic;">{escape(str(patient.get('summary', '')))}</div>
    </div>
    <button onclick="document.querySelector('#hidden-btn-{patient_id} button, #hidden-btn-{patient_id}').click();" style="background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%);color:#0A0E1A;font-family:Inter,sans-serif;font-size:14px;font-weight:600;padding:10px 24px;border:none;border-radius:10px;position:relative;overflow:hidden;transition:all 0.2s ease;box-shadow:0 4px 15px rgba(212,175,55,0.25);" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 25px rgba(212,175,55,0.4)';this.style.animation='btnGlow 1.5s ease-in-out infinite';" onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 15px rgba(212,175,55,0.25)';this.style.animation='none';">Open Patient<div style="position:absolute;top:0;left:-100%;width:50%;height:100%;background:linear-gradient(90deg,rgba(255,255,255,0) 0%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0) 100%);animation:btnShine 3s ease-in-out infinite;"></div></button>
  </div>
</div>
"""
        cards.append(card)

    return f"""
<div style="position: relative;min-height: 100vh;background: linear-gradient(170deg, #0A0E1A 0%, #111827 20%, #1E3A8A 35%, #7C2D12 45%, #D97706 55%, #F8FAFC 65%, #93C5FD 75%, #1E3A8A 85%, #0A0E1A 100%);background-size:100% 300%;animation: gradientFlow 12s ease-in-out infinite;overflow:hidden;">
  <div style="display:flex;align-items:center;padding:20px 40px;position:relative;z-index:10;">
    <img src="/file=frontend/assets/clarke_logo.svg" style="width:44px;height:48px;margin-right:14px;filter:drop-shadow(0 0 8px rgba(212,175,55,0.4));"/>
    <span style="font-family:'DM Serif Display',serif;font-size:32px;color:#D4AF37;">Clarke</span>
    <span style="font-family:Inter,sans-serif;font-size:14px;color:#94A3B8;margin-left:16px;padding-top:8px;">Clinical Documentation Copilot</span>
    <div style="margin-left:auto;display:flex;align-items:center;gap:8px;"><div style="width:8px;height:8px;background:#22C55E;border-radius:50%;animation:recordPulse 3s ease-in-out infinite;"></div><span style="font-family:Inter,sans-serif;font-size:13px;font-weight:500;color:#94A3B8;">Ready</span></div>
  </div>
  <div style="margin:0 40px 32px 40px;padding:16px 24px;background:rgba(255,255,255,0.06);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.08);border-radius:12px;border-left:4px solid #D4AF37;animation:fadeSlideIn 0.6s ease forwards;"><span style="font-family:'DM Serif Display',serif;font-size:20px;color:#F8FAFC;">{escape(str(clinician.get('name', 'Dr. Sarah Chen')))}</span><span style="font-family:Inter,sans-serif;font-size:14px;color:#94A3B8;margin-left:12px;">{escape(str(clinician.get('specialty', 'Specialty')))} — {escape(str(clinic_payload.get('date', '13 February 2026')))}</span></div>
  {''.join(cards)}
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
