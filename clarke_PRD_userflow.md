# Clarke — PRD User Flow

**Version:** 1.0 | **Date:** 13 February 2026 | **Author:** Project Lead  
**Status:** Final — user experience specification for all Clarke UI work  
**Derives from:** clarke_PRD_masterplan.md, Clarke_Product_Specification_V2.md  
**References:** clarke_PRD_design_guidelines.md (visual styling), clarke_PRD_implementation.md (build sequence)  
**Scope:** What the user sees and does at every moment. Does NOT cover visual styling (see design guidelines), build sequence, backend API contracts, or granular coding tasks.

---

## 1. Screen Inventory

Clarke has six distinct screens. The user moves through them in a linear wizard flow (see §5).

| # | Screen | Purpose | Displays | User Actions |
|---|--------|---------|----------|--------------|
| S1 | **Dashboard** | Entry point. Shows today's clinic list. | Clinic header (clinician name, specialty, date), list of patient cards with name, age/sex, time, one-line summary. | Click a patient card to select. |
| S2 | **Patient Context** | Pre-consultation briefing. Shows EHR data retrieved by MedGemma 4B. | Left panel: structured context (diagnoses, medications, allergies, recent labs with trends, recent imaging, flags). Centre panel: empty document area with prompt to start. | Review context. Click "Start Consultation." Click "Back to Dashboard" to return. |
| S3 | **Live Consultation** | Active recording. MedASR transcribes in real-time. | Recording indicator (pulse animation per design guidelines §4.5). Expandable live transcript panel. Patient context still visible on left. Timer showing elapsed recording time. | Pause/resume recording. Expand/collapse transcript. Click "End Consultation." |
| S4 | **Processing** | Pipeline executes: transcription finalisation → context synthesis → document generation. | Three-stage progress bar (per design guidelines §4.8) with stage labels. Elapsed timer. No user actions required — wait state. | None (wait). Cancel button returns to S2 with a confirmation dialog. |
| S5 | **Document Review** | Core screen. Clinician reviews, edits, and approves the generated letter. | Left panel: patient context (collapsed summary). Centre panel: generated NHS clinic letter in paper container (design guidelines §4.6). FHIR-sourced values highlighted in monospace. Discrepancy flags (if any) shown as inline alert badges. Status badge: "Ready for Review." | Inline edit any paragraph. Regenerate a section. View FHIR source for any cited value. Click "Sign Off & Export." Click "Regenerate Entire Letter." Click "Discard Draft" (destructive). |
| S6 | **Signed Off** | Confirmation. Document is approved. Export options available. | Document preview (read-only). Status badge: "Signed Off" (green). Export buttons: PDF, Copy to Clipboard, FHIR DocumentReference. "Next Patient" button. | Export via any method. Click "Next Patient" to return to S1 with next patient highlighted. |

---

## 2. System States

Clarke exists in one of eight states at any time. Each state maps to exactly one screen.

| State | Screen | User Sees | Background Activity | Available Actions | Visual Indicator |
|-------|--------|-----------|--------------------|--------------------|------------------|
| **Idle** | S1 | Dashboard with clinic list. Hero gradient background (design guidelines §1). | None. | Select patient. | No status badge. Warm gradient background. |
| **Patient Selected** | S2 | Patient context loading → populated. | MedGemma 4B queries FHIR server (5–10s). | Start Consultation. Back to Dashboard. | Skeleton loaders during load (design guidelines §4.8) → populated cards on completion. |
| **Recording** | S3 | Recording pulse animation. Live transcript streaming. | MedASR processes audio chunks in real-time. | Pause, Resume, End Consultation. | Gold pulse + rotating ring (design guidelines §4.5). "Recording" status badge. |
| **Paused** | S3 | Pulse animation stops. "Paused" label replaces "Recording…" | Audio capture paused. Transcript preserved. | Resume, End Consultation. | Static gold circle (no pulse). "Paused" badge replaces "Recording" badge. |
| **Processing** | S4 | Three-stage progress bar filling sequentially. | MedASR finalises transcript → MedGemma 4B synthesises context → MedGemma 27B generates letter. ~15–30s total. | Cancel (with confirmation). | Progress bar + "Processing" badge (spinner, blue). Stage labels update. |
| **Review** | S5 | Generated letter in paper container. | None. | Edit, Regenerate section, Sign Off, Discard. | "Ready for Review" badge (amber, pencil icon). Gold left-border on editable sections. |
| **Editing** | S5 | Active paragraph highlighted with edit background (`#FEFDF5`). Cursor active. | None. | Type changes, click away to deselect. | Paragraph highlight + gold left border. |
| **Signed Off** | S6 | Read-only letter. Export buttons. | None. | Export, Next Patient. | "Signed Off" badge (green, checkmark). Document generation reveal animation (design guidelines §5). |

---

## 3. Complete Happy-Path User Journey

Each step below includes: screen, what the user sees, what they do, what happens, and approximate duration.

**Step 1 — Open Clarke (S1, ~3s)**  
User opens Clarke in their browser. The dashboard loads with the hero gradient (design guidelines §1). Their clinic list appears with scroll entrance animation (design guidelines §5). Five patient cards are listed. System is in Idle state.

**Step 2 — Select Patient (S1 → S2, ~1s transition)**  
User clicks Mrs. Thompson's patient card. Card hover shadow deepens (design guidelines §4.2). On click, ripple-shine fires (design guidelines §4.1). Panel transition animation (design guidelines §5) slides dashboard out left and patient context in from right.

**Step 3 — Context Loads (S2, ~5–10s)**  
Skeleton loaders appear in the patient context panel. MedGemma 4B queries FHIR. Skeletons resolve to structured data: diagnoses, medications, allergies (with ⚠ flag), recent labs (HbA1c 55 ↑, eGFR 52 ↓), and clinical flags. The centre panel shows an empty document area with the CTA: "Start Consultation."

**Step 4 — Start Consultation (S2 → S3, ~1s)**  
User clicks "Start Consultation" (primary button, ripple-shine). Browser requests microphone permission (see §6a). Recording indicator transitions from idle (64px, blue mic) to recording (80px, gold mic, pulse + ring animation). Timer begins at 00:00. State transitions to Recording.

**Step 5 — Consultation Happens (S3, ~1–30min)**  
The clinician talks to their patient. Live transcript text streams in the expandable transcript panel (minimised by default). Patient context remains visible on the left for reference. The recording pulse continues. The timer increments.

**Step 6 — End Consultation (S3 → S4, ~1s)**  
User clicks "End Consultation" (primary button). Recording stops. Recording indicator shrinks to 64px, becomes blue spinner. State transitions to Processing.

**Step 7 — Pipeline Processes (S4, ~15–30s)**  
Three-stage progress bar fills sequentially. Stage captions update: "Finalising transcript…" → "Synthesising patient context…" → "Generating clinical letter…" Each segment fills with `--clarke-blue` with pulse glow on the active segment. The user waits.

**Step 8 — Letter Appears (S4 → S5, ~1s)**  
Document generation reveal animation fires (design guidelines §5): gold sparkle flash on document card border, then paper container scales 0.97→1.0 with upward drift and opacity fade-in over 800ms. This is the "ta-da" moment. The NHS-format clinic letter is now visible. Status badge: "Ready for Review."

**Step 9 — Review and Edit (S5, ~30–120s)**  
User reads the letter. FHIR-sourced values (lab results, medication names) appear in monospace font with a subtle blue background tint, indicating they came from the record. User clicks a paragraph to edit inline — the paragraph highlights with gold left border and `#FEFDF5` background. User types their edit. Clicks away to confirm.

**Step 10 — Sign Off (S5 → S6, ~2s)**  
User clicks "Sign Off & Export" (primary button, ripple-shine). A brief confirmation toast appears: "Document approved." Status badge transitions to "Signed Off" (green, checkmark). Export buttons appear: PDF, Copy to Clipboard, FHIR DocumentReference. Document becomes read-only.

**Step 11 — Export and Move On (S6 → S1, ~5s)**  
User clicks an export button (e.g., "Copy to Clipboard"). Success toast: "Copied to clipboard." User clicks "Next Patient." Panel transition slides back to the dashboard with the next patient highlighted.

**Total elapsed time for happy path: ~2–35 minutes** (dominated by the consultation itself; Clarke adds ~60–90 seconds of overhead).

---

## 4. Demo Golden Path (3-Minute Video)

This is the exact sequence shown in the competition video. Pre-loaded synthetic data: Mrs. Margaret Thompson, 67F, Type 2 Diabetes, in HAPI FHIR. Pre-recorded 60-second audio clip of a simulated clinician-patient consultation.

| Timestamp | Screen | On Screen | Narration (voiceover) | Purpose |
|-----------|--------|-----------|----------------------|---------|
| 0:00–0:05 | — | Title card: Clarke logo on hero gradient. Tagline: "3 models. 1 pipeline. Zero data leaves." | *"This is Clarke."* | First impression. Hero gradient moment (design guidelines §8). |
| 0:05–0:15 | S1 | Dashboard. Five patient cards. Warm gradient. | *"NHS doctors spend four hours on admin for every hour with patients. Clarke changes that."* | Problem statement. Visual: polished dashboard. |
| 0:15–0:25 | S1→S2 | Click Mrs. Thompson → context loads via skeleton → structured data appears. | *"Select a patient. Clarke's EHR agent — MedGemma 4B — retrieves their full record from the hospital's FHIR server in seconds."* | Demonstrate Model 1 (MedGemma 4B). |
| 0:25–0:35 | S2→S3 | Click "Start Consultation." Recording pulse activates. | *"Start the consultation. Clarke listens using MedASR, a purpose-built medical speech recognition model."* | Demonstrate Model 2 (MedASR). Recording pulse moment (design guidelines §8). |
| 0:35–1:25 | S3 | Pre-recorded audio plays (~50s). Live transcript streams. Patient context visible. | *"The clinician has their normal conversation. Real-time transcription runs in the background. The patient context panel is always available for reference."* (then silence over audio clip) | Show ambient transcription + EHR context side by side. |
| 1:25–1:35 | S3→S4 | Click "End Consultation." Progress bar fills through three stages. | *"When the consultation ends, Clarke's three-model pipeline activates. Transcript and patient context are fused and sent to MedGemma 27B."* | Demonstrate Model 3 (MedGemma 27B). Pipeline stages visible. |
| 1:35–1:50 | S4→S5 | Gold sparkle → letter reveals. NHS-format clinic letter fills the screen. | *"In under 30 seconds, a complete NHS clinic letter — populated with actual lab values and the current medication list — is ready for review."* Pause narration briefly for the reveal. | Document reveal moment (design guidelines §8). The most important visual beat. |
| 1:50–2:25 | S5 | Scroll through letter. Point out: hyperlinked FHIR values, allergy preserved, assessment + plan from conversation. | *"Every investigation result is hyperlinked to its source record. The letter contains both what was discussed and what exists in the patient's record. No other ambient scribe does this."* | Demonstrate the fusion value — conversation + record context. |
| 2:25–2:45 | S5 | Click a paragraph → inline edit → type an addition → click Sign Off. Status badge turns green. Export buttons appear. | *"The clinician reviews, makes any edits, and signs off. The letter is ready — before the next patient walks in."* | Demonstrate clinician-in-the-loop workflow. |
| 2:45–3:00 | S6→Card | Closing card: "Clarke: 3 HAI-DEF models. 1 pipeline. Zero patient data leaves the building." Links: GitHub, HF Space, HF LoRA. | *"Clarke. Open-source. Privacy-preserving. Built for the NHS."* | Closing. Links for judges to click. |

---

## 5. Navigation Structure

**Pattern: Linear wizard with escape hatches.**

Clarke uses a linear flow (S1 → S2 → S3 → S4 → S5 → S6 → S1) because the clinical workflow is inherently sequential: you pick a patient, consult, document, move on. A hub-and-spoke pattern would add cognitive overhead for a clinician mid-clinic.

**Forward navigation:** Driven by primary action buttons ("Start Consultation," "End Consultation," "Sign Off & Export," "Next Patient"). Each button advances to the next screen.

**Backward navigation:**
- S2 → S1: "Back to Dashboard" secondary button. No data loss.
- S3 → S2: "End Consultation" + discard. Confirmation dialog: "End recording without generating a letter? The recording will be lost." Two options: "End & Discard" (destructive), "Continue Recording" (secondary).
- S5 → S2: "Discard Draft" destructive button. Confirmation dialog: "Discard this draft and start over?" Two options: "Discard" (destructive), "Keep Editing" (secondary).
- S4 → S2: "Cancel" during processing. Confirmation dialog: "Cancel document generation? You can re-record the consultation."

**Abandoning a consultation:** At any point from S2–S5, the sidebar "Dashboard" link is available. Clicking it during an active consultation triggers the appropriate confirmation dialog. No silent data loss.

**No deep linking.** Clarke does not support URL-based navigation to specific screens. The state is held in `gr.State` (Gradio) and resets on page refresh.

---

## 6. Error States and Edge Cases

Each error follows the design guidelines' emotional principle: "Help Has Arrived" — errors are reassuring, not alarming. Error cards use standard card styling with `--clarke-red-light` background tint and `--clarke-red` left border.

| # | Scenario | User Sees | Recovery |
|---|----------|-----------|----------|
| a | **Microphone permission denied / mic not detected** | Inline alert card on S2 (below "Start Consultation" button): "Clarke needs microphone access to record the consultation. Please allow microphone access in your browser settings." Icon: mic-off (Lucide). Button: "Try Again" (re-requests permission). | Retry, or use pre-recorded audio upload fallback (secondary button: "Upload Audio File"). |
| b | **Recording fails / audio quality too poor** | On S4, if MedASR returns empty or near-empty transcript: alert card replaces progress bar: "The audio could not be transcribed. This may be due to background noise or microphone issues." | Two buttons: "Re-record Consultation" (returns to S3), "Upload Audio File." |
| c | **Patient not found in FHIR** | On S2, if FHIR query returns no results: context panel shows empty state card: "No records found for this patient in the EHR system. You can still record a consultation — Clarke will generate a letter from the conversation alone (without EHR context)." | "Start Consultation" remains available. Clarke operates in documentation-only mode. |
| d | **MedGemma 4B returns incomplete context** | On S2, partial context loads with a warning badge at the top: "Some patient records could not be retrieved. Available data is shown below." Missing sections show "Not available" in `--clarke-text-disabled`. | Proceed normally. Document generation uses whatever context was retrieved. |
| e | **MedGemma 27B generates flagged inconsistencies** | On S5, inline discrepancy badges appear within the letter. E.g., a red alert badge next to a sentence: "⚠ Conversation says 'no allergies' but record shows Penicillin allergy." Badge uses `--clarke-red` text on `--clarke-red-light` background. | Clinician reviews and edits the relevant section before signing off. Discrepancy badges must be resolved (edited or dismissed) before "Sign Off" is clickable. |
| f | **Network / model timeout during processing** | On S4, progress bar stalls. After 90 seconds, an alert card replaces the progress bar: "Document generation is taking longer than expected. This may be due to server load." | Two buttons: "Retry" (re-triggers pipeline), "Return to Dashboard." |
| g | **User wants to restart from scratch** | Available on S3 and S5 via destructive actions (see §5 backward navigation). Confirmation dialogs prevent accidental loss. | Confirmation → return to S2 with patient context preserved. |

---

## 7. Loading and Waiting States

| Wait Point | Screen | Duration | User Sees | User Can Act? |
|------------|--------|----------|-----------|---------------|
| **FHIR context retrieval** | S2 | 5–10s | Skeleton loaders matching context panel layout (design guidelines §4.8). Shimmer animation (1.5s cycle). | No. Wait for context. Can click "Back to Dashboard" to abort. |
| **Pipeline processing** | S4 | 15–30s | Three-segment progress bar. Each segment fills as its stage completes. Caption updates: "Finalising transcript…" → "Synthesising patient context…" → "Generating clinical letter…" Active segment pulses with `--clarke-blue` glow. | No active actions. Cancel button available. |
| **Section regeneration** | S5 | 5–10s | The regenerating section shows a skeleton loader in place of the text. Rest of letter remains visible and readable. | Yes — can continue reading/editing other sections while one regenerates. |

---

## 8. Document Review and Editing Interaction

**Document presentation:** The generated letter renders in a paper container (design guidelines §4.6) — max-width 720px, centred, inset shadow. The letter uses NHS clinic letter structure: date, addressee, patient demographics, Re: line, salutation, body sections (HPC, examination, investigations, assessment, plan, medications), sign-off.

**Visual distinction of data sources:**
- **FHIR-sourced values** (lab results, medication names, allergy entries): rendered in monospace font (`JetBrains Mono`, design guidelines §2) with a subtle blue-tinted background (`rgba(43, 94, 167, 0.06)`). On hover, a tooltip shows: "Source: FHIR [Resource Type] / [Date]".
- **AI-generated prose** (narrative text from MedGemma 27B): standard body font. No special marking.
- **Discrepancy flags**: inline `--clarke-red` alert badges (see §6e).

**Editing model: inline editing.**
- Click any paragraph → it becomes editable (contenteditable). Background changes to `#FEFDF5`. Gold left border (3px) appears.
- Type freely. Standard text editing (select, delete, type).
- Click outside the paragraph to save. No explicit save button — changes are immediate.
- "Regenerate" button appears on hover at the right edge of each section header. Clicking it replaces the section content via MedGemma 27B re-generation (see §7 for loading state).

**Sign-off flow:**
1. User clicks "Sign Off & Export."
2. If unresolved discrepancy flags exist → a blocking dialog: "Please review the flagged discrepancies before signing off." Button: "Review Flags" (scrolls to first flag).
3. If no flags → document status transitions to Signed Off. Export buttons appear. Document becomes read-only.

---

## 9. Interaction Micro-Details

| Interaction | Click Target | Immediate Feedback | Next Event |
|-------------|-------------|-------------------|------------|
| **Select patient** (S1) | Patient card | Card shadow deepens + translateY(-2px) on hover. Ripple-shine on click (200ms). | Panel transition to S2 (~300ms). FHIR retrieval begins. |
| **Start Consultation** (S2) | Primary button | Ripple-shine (600ms). Button text changes to "Starting…" briefly. | Recording indicator transitions to active state (64px→80px, pulse begins). Screen transitions to S3. |
| **Pause Recording** (S3) | Pause icon button (44×44px, secondary style) | Pulse animation stops. Icon toggles to play. "Paused" label fades in (200ms). | Audio capture pauses. Timer stops. |
| **Resume Recording** (S3) | Play icon button | Pulse animation resumes. Icon toggles to pause. "Recording…" label fades in. | Audio capture resumes. Timer resumes. |
| **End Consultation** (S3) | Primary button "End Consultation" | Ripple-shine. Recording indicator shrinks (80px→64px, 300ms). Pulse stops. | Transition to S4. Pipeline begins. |
| **Inline edit** (S5) | Any paragraph in the letter | Paragraph background changes to `#FEFDF5`. Gold left border appears (150ms fade-in). Text cursor activates. | User types. Changes saved on click-away. |
| **Regenerate section** (S5) | "Regenerate" icon button (on hover of section header) | Section text replaced by skeleton loader. | MedGemma 27B re-generates section (~5–10s). New text fades in. |
| **Sign Off** (S5) | Primary button "Sign Off & Export" | Ripple-shine. Success toast: "Document approved" (slides down from top, 3s auto-dismiss). Status badge transitions green. | Export buttons appear (fade-in, 300ms). Document becomes read-only. |
| **Export PDF** (S6) | Secondary button "PDF" | Button shows spinner briefly. | PDF generated and downloaded via browser. |
| **Next Patient** (S6) | Primary button | Ripple-shine. | Panel transition back to S1. Next patient in list is highlighted. |

---

## 10. Accessibility Considerations

**Touch targets:** Minimum 44×44px for all interactive elements (per WCAG 2.1 AA and design guidelines §3). Buttons, patient cards, sidebar links, and the recording indicator all meet this minimum.

**Keyboard navigation:** All screens are navigable via Tab (forward) and Shift+Tab (backward). Focus indicators: 3px `--clarke-blue` outline with 2px offset. Enter/Space activates buttons. Escape closes dialogs and exits inline editing.

**Screen readers:** All interactive elements have `aria-label` attributes. Status badges have `role="status"` with `aria-live="polite"` to announce state changes. The recording indicator announces "Recording started" / "Recording paused" / "Recording stopped" via `aria-live`. Progress bar has `role="progressbar"` with `aria-valuenow`.

**Clinical environment considerations:**
- **Gloves:** All targets ≥44px. No precision gestures (no drag-and-drop, no small toggles).
- **Shared workstation:** No persistent login state beyond the browser session. Clarke does not store credentials or patient data locally.
- **Noisy ward:** The UI does not rely on audio feedback. All state changes are communicated visually and via screen reader announcements.
- **Arm's length readability:** Minimum text size 13px (label). All body text ≥16px (design guidelines §2). Key status indicators use colour + icon + text (never colour alone).

---

*This document defines every screen, state, transition, and interaction in Clarke. Implementation details (how to build it) are in clarke_PRD_implementation.md and clarke_PRD_technical_spec.md. Visual styling (what it looks like) is in clarke_PRD_design_guidelines.md. Every interaction described here must trace to those specifications.*
