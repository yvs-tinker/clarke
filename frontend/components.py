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
  @keyframes clarkeGradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  @keyframes btnShine {0% { left: -100%; }50% { left: 100%; }100% { left: 100%; }}
  @keyframes fadeSlideIn {0% { opacity: 0; transform: translateY(20px); }100% { opacity: 1; transform: translateY(0); }}
  @keyframes recordPulse {0%, 100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.6); }50% { box-shadow: 0 0 0 24px rgba(212, 175, 55, 0); }}
  @keyframes progressSpin {0% { transform: rotate(0deg); }100% { transform: rotate(360deg); }}
  @keyframes progressGlow {0%, 100% { opacity: 0.6; }50% { opacity: 1; }}
  @keyframes clarkeLogoShimmer {
    0% { filter: brightness(1) drop-shadow(0 0 3px rgba(212,175,55,0.3)); }
    50% { filter: brightness(1.5) drop-shadow(0 0 12px rgba(255,193,7,0.7)); }
    100% { filter: brightness(1) drop-shadow(0 0 3px rgba(212,175,55,0.3)); }
  }

  html, body { margin: 0 !important; padding: 0 !important; overflow-x: hidden !important; }

  #hidden-select-0, #hidden-select-1, #hidden-select-2, #hidden-select-3, #hidden-select-4,
  #hidden-start-consultation, #hidden-back, #hidden-cancel, #hidden-regenerate, #hidden-copy, #hidden-download,
  #hidden-end-consultation, #hidden-sign-off, #hidden-next-patient {
    display: block !important;
    position: fixed !important;
    top: -9999px !important;
    left: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    overflow: hidden !important;
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
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="(function(){function e(){var a=document.querySelector('gradio-app');if(a){a.style.setProperty('background','#F8F6F1','important');a.style.setProperty('padding','0','important');a.style.setProperty('margin','0','important');a.style.setProperty('overflow-x','hidden','important');}document.querySelectorAll('.gradio-container,[class*=gradio-container-]').forEach(function(c){c.style.setProperty('max-width','100vw','important');c.style.setProperty('padding','0','important');c.style.setProperty('margin','0','important');});document.body.style.setProperty('margin','0','important');document.body.style.setProperty('padding','0','important');document.body.style.setProperty('background','#F8F6F1','important');var f=document.querySelector('footer');if(f)f.style.display='none';}e();[100,300,600,1200,2500,5000].forEach(function(t){setTimeout(e,t);});new MutationObserver(function(){e();}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});console.log('Clarke: Layout enforcer active via img onload');})()" style="display:none;position:absolute;width:0;height:0;">
"""


def build_dashboard_html(clinic_payload: dict[str, Any], completed_patients: list[int] | None = None) -> str:
    """Render the S1 dashboard markup with top gradient and white card area.

    Args:
        clinic_payload (dict[str, Any]): Clinic roster and clinician metadata.

    Returns:
        str: Complete HTML markup for the dashboard screen.
    """

    clinician = clinic_payload.get("clinician", {})
    completed_lookup = set(completed_patients or [])
    cards: list[str] = []
    for index, patient in enumerate(clinic_payload.get("patients", [])):
        click_js = _open_patient_click_js(index)
        completed = index in completed_lookup
        card_style = "opacity:0.55;" if completed else ""
        hover_class = "completed-patient-card" if completed else ""
        badge = "<div style=\"position:absolute;top:12px;right:12px;background:#27ae60;color:white;padding:4px 12px;border-radius:12px;font-family:'Inter',sans-serif;font-size:12px;font-weight:600;\">✓ Complete</div>" if completed else ""
        button_markup = (
            f"<button onclick=\"{click_js}\" style=\"background:transparent;border:2px solid #27ae60;color:#27ae60;padding:8px 20px;border-radius:8px;font-family:'Inter',sans-serif;font-weight:600;cursor:pointer;transition:all 0.3s ease;\" onmouseover=\"this.style.background='rgba(39,174,96,0.1)'\" onmouseout=\"this.style.background='transparent'\">Review Letter</button>"
            if completed
            else f"<button class=\"clarke-btn-gold\" onclick=\"{click_js}\">Open Patient</button>"
        )
        cards.append(
            f"""
<div class="patient-card {hover_class}" style="background:rgba(255,255,255,0.95);border:1px solid rgba(212,175,55,0.12);border-radius:16px;padding:24px 28px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.04);animation:fadeSlideIn 0.5s ease forwards;animation-delay:{index * 0.1}s;opacity:0;{card_style}">
  {badge}
  <div style="position:absolute;left:0;top:0;width:3px;height:100%;background:linear-gradient(180deg,#D4AF37,#F0D060);"></div>
  <div style="display:flex;justify-content:space-between;align-items:center;gap:16px;">
    <div>
      <div style="font-family:'Inter',sans-serif;font-size:12px;font-weight:600;color:#D4AF37;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">{escape(str(patient.get('time', '--:--')))}</div>
      <div style="font-family:'DM Serif Display',serif;font-size:20px;color:#1A1A2E;margin-bottom:4px;">{escape(str(patient.get('name', 'Unknown patient')))}</div>
      <div style="font-family:'Inter',sans-serif;font-size:14px;color:#555;margin-bottom:2px;">{escape(str(patient.get('age', '')))} · {escape(str(patient.get('sex', '')))}</div>
      <div style="font-family:'Inter',sans-serif;font-size:14px;color:#555;font-style:italic;">{escape(str(patient.get('summary', '')))}</div>
    </div>
    {button_markup}
  </div>
</div>
"""
        )

    return f"""
<style>
@keyframes clarkeGradientShift {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
.completed-patient-card:hover {{ opacity: 0.7 !important; box-shadow: 0 4px 14px rgba(0,0,0,0.08) !important; transform: translateY(-2px) scale(1.005) !important; }}
@keyframes clarkeShimmerDrift1 {{
  0% {{ transform: translate(0, 0) scale(1); opacity: 0.7; }}
  50% {{ transform: translate(5%, 8%) scale(1.1); opacity: 1; }}
  100% {{ transform: translate(0, 0) scale(1); opacity: 0.7; }}
}}
@keyframes clarkeShimmerDrift2 {{
  0% {{ transform: translate(0, 0) scale(1); opacity: 0.6; }}
  50% {{ transform: translate(-6%, -5%) scale(1.15); opacity: 1; }}
  100% {{ transform: translate(0, 0) scale(1); opacity: 0.6; }}
}}
@keyframes clarkeShimmerDrift3 {{
  0% {{ transform: translate(0, 0) scale(1); opacity: 0.5; }}
  50% {{ transform: translate(4%, -6%) scale(1.08); opacity: 1; }}
  100% {{ transform: translate(0, 0) scale(1); opacity: 0.5; }}
}}
</style>
<div id="clarke-app-wrapper" style="min-height: 100vh; margin: 0; padding: 0; background: #F8F6F1; position: relative; overflow: hidden;">
  <!-- Golden sunlight shimmer layers -->
  <div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;overflow:hidden;">
    <div style="position:absolute;top:-20%;left:-10%;width:60%;height:50%;background:radial-gradient(ellipse at center, rgba(255,193,7,0.06) 0%, rgba(255,193,7,0) 70%);animation:clarkeShimmerDrift1 12s ease-in-out infinite;"></div>
    <div style="position:absolute;top:30%;right:-15%;width:55%;height:45%;background:radial-gradient(ellipse at center, rgba(212,175,55,0.05) 0%, rgba(212,175,55,0) 70%);animation:clarkeShimmerDrift2 16s ease-in-out infinite;"></div>
    <div style="position:absolute;bottom:-10%;left:20%;width:50%;height:40%;background:radial-gradient(ellipse at center, rgba(255,179,0,0.04) 0%, rgba(255,179,0,0) 70%);animation:clarkeShimmerDrift3 14s ease-in-out infinite;"></div>
    <div style="position:absolute;top:10%;left:40%;width:40%;height:35%;background:radial-gradient(ellipse at center, rgba(255,215,64,0.045) 0%, rgba(255,215,64,0) 65%);animation:clarkeShimmerDrift1 18s ease-in-out infinite reverse;"></div>
  </div>
  <div style="position:relative;z-index:1;padding:32px 48px 24px 48px;">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
      <div style="display:inline-block;">
        <svg width="56" height="48" viewBox="0 0 56 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Superman-style: wide flat top, long angled sides, sharp bottom point -->
          <path d="M2 2 L54 2 L52 6 L28 46 L4 6 Z" fill="#B8941F" />
          <path d="M6 5 L50 5 L48 8 L28 42 L8 8 Z" fill="#D4AF37" />
          <path d="M9 7.5 L47 7.5 L45.5 10 L28 39 L10.5 10 Z" fill="#D4AF37" />
        </svg>
      </div>
      <span style="font-family:'DM Serif Display',serif; font-size:32px; color:#D4AF37; font-weight:400;">Clarke</span>
    </div>
    <div style="padding:14px 22px;background:rgba(212,175,55,0.06);backdrop-filter:blur(12px);border:1px solid rgba(212,175,55,0.15);border-radius:12px;border-left:4px solid #D4AF37;">
      <span style="font-family:'DM Serif Display',serif;font-size:20px;color:#1A1A2E;">{escape(str(clinician.get('name', 'Dr. Sarah Chen')))}</span>
      <span style="font-family:'Inter',sans-serif;font-size:14px;color:#555;margin-left:12px;">{escape(str(clinician.get('specialty', 'General Practice')))} — {escape(str(clinic_payload.get('date', '13 February 2026')))}</span>
    </div>
  </div>
  <div id="clarke-content-area" style="position:relative;z-index:1;background:transparent;margin:0;padding:32px 48px;min-height:70vh;">
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
