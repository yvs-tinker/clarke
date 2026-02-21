"""HTML builders for Clarke frontend screens."""

from __future__ import annotations

from datetime import date
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
</style>
<style>
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

  /* Letter Preferences Accordion */
  #clarke-letter-prefs {
    margin: 0 48px 24px 48px !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.65) !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
  }
  #clarke-letter-prefs > .label-wrap {
    padding: 14px 20px !important;
    background: transparent !important;
    border: none !important;
    border-bottom: none !important;
    cursor: pointer !important;
  }
  #clarke-letter-prefs > .label-wrap span {
    font-family: 'DM Serif Display', serif !important;
    font-size: 16px !important;
    color: #D4AF37 !important;
  }
  #clarke-letter-prefs > .label-wrap:hover {
    background: rgba(212, 175, 55, 0.04) !important;
  }
  #clarke-letter-prefs input[type="text"],
  #clarke-letter-prefs textarea {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    border: 1px solid rgba(212, 175, 55, 0.2) !important;
    border-radius: 8px !important;
    background: rgba(255, 255, 255, 0.85) !important;
    color: #1A1A2E !important;
    padding: 10px 14px !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
  }
  #clarke-letter-prefs input[type="text"]:focus,
  #clarke-letter-prefs textarea:focus {
    border-color: #D4AF37 !important;
    box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.12) !important;
    outline: none !important;
  }
  #clarke-letter-prefs label span {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #555 !important;
  }

  /* Letter Preferences Accordion */
  #clarke-letter-prefs {
    margin: 0 48px 24px 48px !important;
    border: 1px solid rgba(212, 175, 55, 0.2) !important;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(8px) !important;
    overflow: hidden !important;
  }
  #clarke-letter-prefs > .label-wrap {
    padding: 14px 20px !important;
    background: transparent !important;
    border: none !important;
    cursor: pointer !important;
  }
  #clarke-letter-prefs > .label-wrap > span {
    font-family: 'DM Serif Display', serif !important;
    font-size: 16px !important;
    color: #D4AF37 !important;
  }
  #clarke-letter-prefs > .label-wrap:hover {
    background: rgba(212, 175, 55, 0.04) !important;
  }
  #clarke-letter-prefs .wrap {
    padding: 4px 20px 16px 20px !important;
    border-top: 1px solid rgba(212, 175, 55, 0.12) !important;
  }
  #clarke-letter-prefs input[type="text"],
  #clarke-letter-prefs textarea {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    border: 1px solid rgba(212, 175, 55, 0.2) !important;
    border-radius: 8px !important;
    background: rgba(255, 255, 255, 0.8) !important;
    color: #1A1A2E !important;
    padding: 10px 14px !important;
    transition: all 0.3s ease !important;
  }
  #clarke-letter-prefs input[type="text"]:focus,
  #clarke-letter-prefs textarea:focus {
    border-color: #D4AF37 !important;
    box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.15) !important;
    outline: none !important;
  }
  #clarke-letter-prefs label span {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #555 !important;
  }

  /* Document Type Radio — matches Letter Preferences */
  fieldset#clarke-doc-type,
  #clarke-doc-type {
    --block-border-width: 0px !important;
    --block-border-color: transparent !important;
    --border-color-primary: transparent !important;
    --block-background-fill: transparent !important;
    --block-shadow: none !important;
    --block-radius: 12px !important;
    margin: 0 48px 16px 48px !important;
    border: 1px solid rgba(212, 175, 55, 0.2) !important;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
    padding: 0 !important;
    overflow: hidden !important;
  }
  fieldset#clarke-doc-type > div,
  #clarke-doc-type > div,
  #clarke-doc-type .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
  }
  #clarke-doc-type > span[data-testid="block-info"] {
    font-family: 'DM Serif Display', serif !important;
    font-size: 16px !important;
    color: #D4AF37 !important;
    padding: 14px 20px 8px 20px !important;
    display: block !important;
  }
  #clarke-doc-type > div.wrap {
    padding: 4px 20px 16px 20px !important;
    border-top: 1px solid rgba(212, 175, 55, 0.12) !important;
    background: transparent !important;
    gap: 12px !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: none !important;
    box-shadow: none !important;
  }
  fieldset#clarke-doc-type label,
  #clarke-doc-type label {
    font-family: 'DM Serif Display', serif !important;
    font-size: 14px !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    background: rgba(255, 255, 255, 0.6) !important;
    color: #555 !important;
  }
  #clarke-doc-type label.selected {
    background: rgba(212, 175, 55, 0.12) !important;
    border-color: #D4AF37 !important;
    color: #1A1A2E !important;
    font-weight: 600 !important;
  }
  #clarke-doc-type label:hover {
    background: rgba(212, 175, 55, 0.06) !important;
    border-color: rgba(212, 175, 55, 0.4) !important;
  }
  #clarke-doc-type input[type="radio"] {
    accent-color: #D4AF37 !important;
  }
  #clarke-doc-type *:not(label):not(input):not(span) {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
  }
  #clarke-doc-type > div[class*="form"],
  #clarke-doc-type > div[class*="svelte"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    overflow: visible !important;
  }

  /* Make Gradio progress bar gold instead of red */
  .progress-bar, .progress-bar > .progress-bar-wrap, .progress-bar > .progress-bar-wrap > .progress-bar-fill {
    background: linear-gradient(135deg, #D4AF37, #F0D060) !important;
  }
  .eta-bar { background: rgba(212, 175, 55, 0.15) !important; }
  /* Hide Gradio error toasts */
  .toast-wrap, .toast-body, .error { display: none !important; }

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

  #clarke-sunrise-glow {
    display: block !important;
    opacity: 1 !important;
    visibility: visible !important;
  }
  #clarke-audio-input {
    max-width: 420px !important;
    margin: 24px auto 0 auto !important;
    border-radius: 16px !important;
    background: rgba(255,255,255,0.85) !important;
    border: 2px solid rgba(212,175,55,0.4) !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 20px rgba(212,175,55,0.12) !important;
    backdrop-filter: blur(8px) !important;
  }
  #clarke-audio-input, #clarke-audio-input * {
    font-family: Inter, sans-serif !important;
  }
  #clarke-audio-input .label-wrap span {
    color: #1A1A2E !important;
    font-family: Inter, sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.03em !important;
  }
  /* Gold control bar */
  #clarke-audio-input .controls {
    background: linear-gradient(135deg, rgba(212,175,55,0.12) 0%, rgba(240,208,96,0.12) 100%) !important;
    border-radius: 12px !important;
    padding: 8px 16px !important;
    border: 1px solid rgba(212,175,55,0.25) !important;
    backdrop-filter: blur(4px) !important;
  }
  /* Buttons inside audio — rounded rect not circles */
  #clarke-audio-input .icon-button,
  #clarke-audio-input .action,
  #clarke-audio-input .play-pause-button,
  #clarke-audio-input .playback,
  #clarke-audio-input .rewind,
  #clarke-audio-input .skip {
    background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%) !important;
    border: none !important;
    color: #1A1A2E !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
  }
  #clarke-audio-input .icon-button:hover,
  #clarke-audio-input .action:hover,
  #clarke-audio-input .play-pause-button:hover {
    box-shadow: 0 2px 12px rgba(212,175,55,0.4) !important;
    transform: scale(1.05) !important;
  }
  /* Gold waveform glow */
  #clarke-audio-input .waveform-container {
    border-radius: 8px !important;
    box-shadow: 0 0 12px rgba(212,175,55,0.15) !important;
  }
  #clarke-audio-input canvas {
    filter: sepia(0.5) saturate(2.5) hue-rotate(15deg) brightness(1.1) !important;
  }
  /* Hide mic-select dropdown ("No microphone found") */
  #clarke-audio-input select.mic-select,
  #clarke-audio-input .mic-select {
    display: none !important;
  }
  /* Record button gold styling */
  #clarke-audio-input .component-wrapper button {
    background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%) !important;
    border: none !important;
    color: #1A1A2E !important;
    border-radius: 8px !important;
    font-family: Inter, sans-serif !important;
    font-weight: 600 !important;
  }
  /* Hide download and share icons but keep clear/X button */
  #clarke-audio-input .icon-button-wrapper.top-panel .download-link,
  #clarke-audio-input .icon-button-wrapper.top-panel button[aria-label="Share"] {
    display: none !important;
  }
  /* Style the clear/X button as re-record */
  #clarke-audio-input .icon-button-wrapper.top-panel button[aria-label='Clear'] {
    background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: #1A1A2E !important;
    padding: 4px 8px !important;
    cursor: pointer !important;
  }
  #clarke-audio-input .icon-button-wrapper.top-panel button[aria-label='Clear']:hover {
    box-shadow: 0 2px 12px rgba(212,175,55,0.4) !important;
    transform: scale(1.05) !important;
  }
  /* Hide trim/scissors and re-record circle buttons in bottom controls */
  #clarke-audio-input .controls .action.icon:last-child {
    display: none !important;
  }
  /* End Consultation button font */
  #clarke-end-consultation-btn {
    font-family: Inter, sans-serif !important;
  }
  /* End Consultation button states */
  .clarke-end-btn-disabled {
    background: rgba(255,255,255,0.6) !important;
    backdrop-filter: blur(12px) !important;
    border: 2px solid rgba(212,175,55,0.2) !important;
    color: rgba(26,26,46,0.4) !important;
    cursor: not-allowed !important;
    pointer-events: none !important;
    box-shadow: none !important;
  }
  .clarke-end-btn-ready {
    background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%) !important;
    color: #1A1A2E !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    box-shadow: 0 -4px 16px rgba(212,175,55,0.3) !important;
    animation: clarkeGoldPulse 2s ease-in-out infinite !important;
  }
  @keyframes clarkeSpin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  @keyframes clarkeGoldPulse {
    0%, 100% { box-shadow: 0 -4px 16px rgba(212,175,55,0.3); }
    50% { box-shadow: 0 -4px 28px rgba(212,175,55,0.6); }
  }
</style>
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" onload="(function(){function e(){document.documentElement.style.setProperty('background','#F8F6F1','important');var a=document.querySelector('gradio-app');if(a){a.style.setProperty('background','transparent','important');a.style.setProperty('padding','0','important');a.style.setProperty('margin','0','important');a.style.setProperty('overflow-x','hidden','important');}document.querySelectorAll('.gradio-container,[class*=gradio-container-]').forEach(function(c){c.style.setProperty('max-width','100vw','important');c.style.setProperty('padding','0','important');c.style.setProperty('margin','0','important');c.style.setProperty('background','transparent','important');});document.body.style.setProperty('margin','0','important');document.body.style.setProperty('padding','0','important');document.body.style.setProperty('background','transparent','important');var f=document.querySelector('footer');if(f)f.style.display='none';}if(!document.getElementById('clarke-sunrise-glow')){var s=document.createElement('style');s.textContent='@keyframes clarkeWarmthPulse{0%{opacity:0.55;transform:scaleY(1) scaleX(1);}50%{opacity:1;transform:scaleY(1.35) scaleX(1.12);}100%{opacity:0.55;transform:scaleY(1) scaleX(1);}}';document.head.appendChild(s);var g=document.createElement('div');g.id='clarke-sunrise-glow';g.style.cssText='position:fixed;top:0;left:0;width:100vw;height:600px;pointer-events:none;z-index:0;background:radial-gradient(ellipse 140% 110% at 50% 0%, rgba(255,193,7,0.80) 0%, rgba(255,213,79,0.55) 20%, rgba(212,175,55,0.28) 45%, transparent 75%);animation:clarkeWarmthPulse 8s ease-in-out infinite;transform-origin:top center;';document.body.insertBefore(g,document.body.firstChild);console.log('Clarke: Sunrise glow injected');}window.clarkePrintPDF=function(){var el=document.getElementById('signed-letter-text');var text='';if(el){text=el.innerText||el.textContent;}if(!text){alert('No letter text found');return;}text=text.trim();var headings=['Summary','History Of Presenting Complaint','Past Medical History','Current Medications','Examination Findings','Investigation Results','Assessment','Plan','Advice To Patient','Assessment And Plan','History of Presenting Complaint','Examination','Investigations','Advice to patient'];var lines=text.split('\\n');var css='@page{size:A4;margin:25mm 20mm 25mm 20mm;}body{font-family:Helvetica,Arial,sans-serif;font-size:12pt;line-height:1.6;color:#1a1a2e;margin:0;padding:0;}.hdr{border-top:3px solid #D4AF37;margin-bottom:8px;}.trust{text-align:right;color:#888;font-size:12pt;margin-bottom:16px;}.gl{border-top:1.5px solid #D4AF37;margin:12px 0;}.sh{font-weight:bold;font-size:14pt;color:#1a1a2e;margin-top:20px;margin-bottom:4px;border-bottom:2px solid #D4AF37;display:inline-block;padding-bottom:2px;}.rl{font-weight:bold;font-size:13pt;}.pi{margin-left:12px;}.so{margin-top:24px;}.sn{font-weight:bold;}.ft{margin-top:40px;text-align:center;color:#bbb;font-size:9pt;}';var h='<!DOCTYPE html><html><head><style>'+css+'</style></head><body>';h+='<div class=hdr></div>';h+='<div class=trust>Clarke NHS Trust<br>General Practice Department<br>University Hospital London</div>';h+='<div class=gl></div>';var inSignoff=false;for(var i=0;i<lines.length;i++){var line=lines[i].trim();if(!line){h+='<br>';continue;}var isH=false;for(var j=0;j<headings.length;j++){if(line===headings[j]){isH=true;break;}}if(isH){h+='<div class=sh>'+line+'</div>';continue;}if(line.match(/^Re:/)){h+='<div class=rl>'+line+'</div>';continue;}if(line.match(/^Warm regards/)||line.match(/^Yours sincerely/)){inSignoff=true;h+='<div class=so>'+line+'</div>';continue;}if(inSignoff){h+='<div class=sn>'+line+'</div>';continue;}if(line.match(/^\d+\./)){h+='<div class=pi>'+line+'</div>';continue;}h+='<div>'+line+'</div>';}h+='<div class=ft>Generated by Clarke - AI Clinical Documentation System</div></body></html>';var iframe=document.createElement('iframe');iframe.style.cssText='position:fixed;top:-9999px;left:-9999px;width:210mm;height:297mm;';document.body.appendChild(iframe);iframe.contentDocument.open();iframe.contentDocument.write(h);iframe.contentDocument.close();setTimeout(function(){iframe.contentWindow.print();setTimeout(function(){document.body.removeChild(iframe);},2000);},500);console.log('Clarke: Print PDF dialog opened');};console.log('Clarke: clarkePrintPDF registered');e();[100,300,600,1200,2500,5000].forEach(function(t){setTimeout(e,t);});new MutationObserver(function(){e();}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});console.log('Clarke: Layout enforcer active via img onload');})()" style="display:none;position:absolute;width:0;height:0;">
"""


def build_dashboard_html(clinic_payload: dict[str, Any], completed_patients: list[int] | None = None) -> str:
    """Render the S1 dashboard markup with top gradient and white card area.

    Args:
        clinic_payload (dict[str, Any]): Clinic roster and clinician metadata.

    Returns:
        str: Complete HTML markup for the dashboard screen.
    """

    clinician = clinic_payload.get("clinician", {})
    _today = date.today().strftime("%d %B %Y")
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
@keyframes clarkeWarmth {{
  0% {{ opacity: 0.6; transform: scaleY(1) scaleX(1); }}
  50% {{ opacity: 1; transform: scaleY(1.2) scaleX(1.05); }}
  100% {{ opacity: 0.6; transform: scaleY(1) scaleX(1); }}
}}
</style>
<div id="clarke-app-wrapper" style="min-height:100vh;margin:0;padding:0;background:transparent;position:relative;">
  <div style="position:relative;z-index:1;padding:32px 48px 24px 48px;">
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="display:inline-block;">
          <svg width="48" height="44" viewBox="0 0 100 90" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 5-sided Superman pentagon: flat top, wide shoulders, long sides, bottom point -->
            <!-- Outer border (gold) -->
            <path d="M20,2 L80,2 L98,28 L50,88 L2,28 Z" fill="#D4AF37"/>
            <!-- Gap (warm white) -->
            <path d="M26,8 L74,8 L89,30 L50,80 L11,30 Z" fill="#F8F6F1"/>
            <!-- Inner fill (gold, matches Clarke text) -->
            <path d="M31,14 L69,14 L82,32 L50,73 L18,32 Z" fill="#D4AF37"/>
          </svg>
        </div>
        <span style="font-family:'DM Serif Display',serif; font-size:32px; color:#D4AF37; font-weight:400;">Clarke</span>
      </div>
      <div style="position:relative;">
        <input id="clarke-patient-search" type="text" placeholder="Search patients..." oninput="(function(v){{document.querySelectorAll('.patient-card').forEach(function(c){{var t=c.innerText.toLowerCase();c.style.display=t.includes(v.toLowerCase())?'':'none';}});}})(this.value)" style="padding:10px 16px 10px 38px;border:1px solid rgba(212,175,55,0.25);border-radius:10px;background:rgba(255,255,255,0.8);backdrop-filter:blur(8px);font-family:'DM Serif Display',serif;font-size:15px;color:#1A1A2E;width:240px;outline:none;transition:all 0.3s ease;" onfocus="this.style.borderColor='#D4AF37';this.style.boxShadow='0 0 12px rgba(212,175,55,0.15)'" onblur="this.style.borderColor='rgba(212,175,55,0.25)';this.style.boxShadow='none'" />
        <span style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#D4AF37;font-size:15px;pointer-events:none;">&#128269;</span>
      </div>
    </div>
    <div style="padding:14px 22px;background:rgba(212,175,55,0.06);backdrop-filter:blur(12px);border:1px solid rgba(212,175,55,0.15);border-radius:12px;border-left:4px solid #D4AF37;">
      <span style="font-family:'DM Serif Display',serif;font-size:20px;color:#1A1A2E;">{escape(str(clinician.get('name', 'Dr. Sarah Chen')))}</span>
      <span style="font-family:'Inter',sans-serif;font-size:14px;color:#555;margin-left:12px;">{escape(str(clinician.get('specialty', 'General Practice')))} — {escape(_today)}</span>
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
