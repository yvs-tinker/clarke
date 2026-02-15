# Clarke — PRD Design Guidelines

**Version:** 1.0 | **Date:** 13 February 2026 | **Author:** Project Lead  
**Status:** Final — visual and emotional specification for all Clarke UI work  
**Derives from:** clarke_PRD_masterplan.md  
**Scope:** What Clarke looks like and feels like. Does NOT cover user flow, screen logic, or technical stack.

---

## 1. Colour Palette

Clarke's palette is extracted from the Superman poster colour language (deep blue, warm gold, vibrant red, bright white) and applied through the soft, atmospheric gradient treatment seen on Sarvam AI's landing page. Colours are never used as flat bold blocks — they appear in gradients, backgrounds, and subtle accents that feel warm and light.

### Core Tokens

| Token | Hex | Usage | Rationale |
|---|---|---|---|
| `--clarke-blue` | `#1E3A5F` | Primary accent. Buttons, active states, links, sidebar active indicators. | Superman suit blue — deep, trustworthy, authoritative but not cold. |
| `--clarke-blue-light` | `#2B5EA7` | Hover states, secondary emphasis, icon fills. | Mid-tone that bridges the deep blue to lighter backgrounds. |
| `--clarke-gold` | `#D4A035` | Secondary accent. Key metrics, success highlights, recording indicator ring, the Clarke logo mark. | Superman emblem gold — warmth, value, something precious. |
| `--clarke-gold-light` | `#F0D078` | Subtle gold highlights, badge backgrounds, warm gradient stops. | Softer gold for backgrounds that shouldn't compete with text. |
| `--clarke-red` | `#C0392B` | Error/alert states ONLY. Critical flags, allergy mismatch badges, destructive button backgrounds. | Superman cape red — used sparingly. Red = something needs your attention NOW. |
| `--clarke-red-light` | `#F5B7B1` | Error state background tints (e.g., alert card background). | Softened red for non-aggressive error containers. |
| `--clarke-white` | `#FFFFFF` | Card surfaces, input backgrounds, modal overlays. | Superman backlighting — brightness, clarity, openness. |
| `--clarke-bg-primary` | `#FAFBFD` | Main page background. | Near-white with a cool whisper — feels like a room with natural light. |
| `--clarke-bg-warm` | `#FFF8F0` | Warm background sections (e.g., hero areas, welcome states). | Warm undertone for sections that should feel inviting. |
| `--clarke-text-primary` | `#1A1A2E` | Headings, body text, primary labels. | Near-black with a slight blue undertone — softer than pure #000. |
| `--clarke-text-secondary` | `#5A6178` | Captions, metadata, secondary labels, timestamps. | Medium-weight grey-blue. Legible but clearly subordinate. |
| `--clarke-text-disabled` | `#A0A8B8` | Disabled inputs, placeholder text. | Light enough to read as inactive. |
| `--clarke-border` | `#E2E6EE` | Card borders, dividers, input outlines at rest. | Subtle. Structures the layout without visual noise. |
| `--clarke-success` | `#27AE60` | "Signed off" badges, success toasts, completed pipeline stages. | Standard accessible green. |
| `--clarke-warning` | `#E67E22` | "Needs review" badges, attention-required states. | Amber — unmissable without implying danger. |

### Gradient Specifications

**Hero gradient (main background):** Applied behind the top section of the dashboard and the welcome/landing state. Mimics Sarvam AI's warm-to-cool atmospheric wash.

```
background: linear-gradient(
  165deg,
  #FDE8C8 0%,    /* warm peach-gold — Superman golden-hour light */
  #F5E6D8 25%,   /* soft warm sand */
  #EEF0F8 55%,   /* cool transition */
  #E8ECF8 80%,   /* light lavender-blue — Superman suit undertone */
  #FAFBFD 100%   /* fades into page background */
);
```

**Sidebar gradient:**
```
background: linear-gradient(
  180deg,
  #1E3A5F 0%,    /* clarke-blue */
  #162D4A 100%   /* deeper blue */
);
```

**Recording active glow:** A radial gradient behind the recording indicator:
```
background: radial-gradient(
  circle,
  rgba(212, 160, 53, 0.25) 0%,   /* gold glow */
  rgba(212, 160, 53, 0.0) 70%    /* fades to transparent */
);
```

---

## 2. Typography System

Benchmark: Sarvam AI's bold, confident headings with clean body text. Every text element must be readable by a tired clinician at arm's length on a standard 1080p monitor.

### Font Stack

- **Primary:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`  
  Inter is chosen for its excellent legibility at all sizes, open-source availability, and medical/professional tone. If Inter cannot be loaded (Gradio constraint), the system stack provides equivalent quality.
- **Monospace (clinical values, codes, FHIR data):** `'JetBrains Mono', 'Fira Code', 'Consolas', monospace`

### Type Scale

| Element | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|
| H1 | 32px | 700 (Bold) | 1.25 | -0.02em | Page titles: "Dashboard", "Mrs Thompson — Consultation" |
| H2 | 24px | 700 (Bold) | 1.3 | -0.01em | Section titles: "Patient Context", "Draft Letter" |
| H3 | 20px | 600 (Semi-Bold) | 1.35 | 0 | Sub-section titles: "Medications", "Recent Bloods" |
| H4 | 17px | 600 (Semi-Bold) | 1.4 | 0 | Card titles, panel labels |
| Body | 16px | 400 (Regular) | 1.6 | 0 | All standard body text. This is the MINIMUM. |
| Body Strong | 16px | 600 (Semi-Bold) | 1.6 | 0 | Inline emphasis within body text |
| Caption | 14px | 400 (Regular) | 1.5 | 0.01em | Timestamps, metadata, help text |
| Label | 13px | 600 (Semi-Bold) | 1.4 | 0.04em | Form labels, badge text, uppercase labels |
| Mono | 15px | 400 (Regular) | 1.5 | 0 | Lab values: "HbA1c: 55 mmol/mol", FHIR codes |

**Non-negotiable rules:**  
- No text below 13px anywhere in the UI.  
- Headings always use weight ≥600. No light or thin headings.  
- Body text line-height ≥1.5. Clinicians scan; dense paragraphs kill readability.

---

## 3. Spacing and Layout System

Reference: Sarvam AI's generous white space. Content must breathe. If it feels like a dense EHR dashboard, something is wrong.

### Spacing Scale (8px base unit)

| Token | Value | Usage |
|---|---|---|
| `--space-xs` | 4px | Inner padding for badges, tight icon gaps |
| `--space-sm` | 8px | Gap between inline elements, icon-to-label spacing |
| `--space-md` | 16px | Standard padding inside cards, between form elements |
| `--space-lg` | 24px | Section separation within a panel, card padding |
| `--space-xl` | 32px | Major section gaps, between cards in a list |
| `--space-2xl` | 48px | Page-level top/bottom padding, hero section padding |
| `--space-3xl` | 64px | Landing/welcome state vertical breathing room |

### Layout Constraints

- **Max content width:** 1280px, centered. Prevents text lines from becoming unreadably long on wide monitors.
- **Sidebar width:** 260px fixed. Collapses to 64px (icon-only) on screens <1024px.
- **Main content area:** Flexible, fills remaining width. Uses a 12-column implicit grid with 24px gutters.
- **Card internal padding:** 24px all sides (--space-lg).
- **Card gap (in a list or grid):** 16px (--space-md).
- **Minimum touch/click target:** 44px × 44px (WCAG).

---

## 4. Component Styling Guidelines

### 4.1 Buttons

**Primary button** — the main action (e.g., "Start Consultation", "Sign Off & Export"):
- Background: `--clarke-blue` (#1E3A5F)
- Text: white, 16px, weight 600
- Border-radius: 12px
- Padding: 12px 24px
- Hover: background shifts to `--clarke-blue-light` (#2B5EA7), subtle scale(1.02) transform
- Active/click: **Ripple-shine effect** — a circular white radial gradient (opacity 0.3) expands from the click point to the button edges over 400ms with `ease-out`, then fades to 0 opacity over 200ms. CSS: use a `::after` pseudo-element with `@keyframes ripple`.
- Disabled: background #A0A8B8, no ripple

**Secondary button** (e.g., "Cancel", "Back"):
- Background: transparent
- Border: 1.5px solid `--clarke-border`
- Text: `--clarke-text-primary`, 16px, weight 500
- Hover: background `#F0F2F8`, border darkens to `--clarke-text-secondary`

**Destructive button** (e.g., "Discard Draft"):
- Background: transparent
- Border: 1.5px solid `--clarke-red`
- Text: `--clarke-red`
- Hover: background `--clarke-red-light`, text `--clarke-red`
- Click: same ripple-shine but with red-tinted radial (#C0392B at opacity 0.15)

### 4.2 Cards

**Standard card** (patient card, document card, context section):
- Background: `--clarke-white`
- Border: 1px solid `--clarke-border`
- Border-radius: 16px
- Box-shadow: `0 1px 3px rgba(26, 26, 46, 0.06), 0 1px 2px rgba(26, 26, 46, 0.04)`
- Padding: 24px
- Hover (if clickable): shadow deepens to `0 4px 12px rgba(26, 26, 46, 0.1)`, translate Y -2px. Transition: 200ms ease

**Patient card** (in patient list): Standard card + left border accent:
- Left border: 4px solid `--clarke-blue`
- Contains: Patient name (H4), NHS number (caption), age/sex badge, brief summary (body)

**Document card** (generated letter preview): Standard card + status badge top-right:
- Status badge (see §4.3) positioned absolute top-right with 12px offset

### 4.3 Status Badges

All badges: border-radius 20px (pill shape), padding 4px 12px, font 13px weight 600, uppercase letter-spacing 0.04em.

| Status | Background | Text | Border | Icon |
|---|---|---|---|---|
| Recording | `rgba(212, 160, 53, 0.15)` | `#8B6914` | none | Pulsing filled circle (see §5) |
| Processing | `rgba(43, 94, 167, 0.12)` | `--clarke-blue` | none | Spinning loader |
| Ready for Review | `rgba(230, 126, 34, 0.12)` | `#B35F00` | none | Pencil/edit icon |
| Signed Off | `rgba(39, 174, 96, 0.12)` | `#1B7A42` | none | Checkmark |

### 4.4 Input Fields

- Background: `--clarke-white`
- Border: 1.5px solid `--clarke-border`
- Border-radius: 10px
- Padding: 12px 16px
- Font: 16px body
- Focus: border-color transitions to `--clarke-blue`, outer box-shadow `0 0 0 3px rgba(30, 58, 95, 0.12)`. Transition: 150ms ease
- Placeholder: `--clarke-text-disabled`, italic

### 4.5 Consultation Recording Indicator

This is Clarke's centrepiece interaction — the visual element most visible in the video demo. It must feel alive and dynamic.

**Idle state:** A circular button (64px diameter) with a microphone icon in `--clarke-blue`. Background white, border `--clarke-border`.

**Recording state:**
- The circle expands to 80px, background becomes `--clarke-gold` with a white microphone icon.
- **Pulse animation:** The circle emits a soft radial glow that scales from 1.0 to 1.3 and fades from opacity 0.4 to 0 over 2 seconds, repeating infinitely. Easing: `ease-in-out`. This is the "heartbeat" — it makes the product feel alive.
- **Colour ring:** A 3px ring orbits the circle (conic-gradient from `--clarke-gold` to `--clarke-blue` to `--clarke-gold`), rotating 360° over 3 seconds. This adds visual richness that reads well on video.
- An adjacent label reads "Recording…" in `--clarke-gold`, 14px, weight 600, with an opacity animation pulsing between 0.6 and 1.0 over 1.5s.

**Processing state (after recording stops):** The circle shrinks back to 64px, background becomes `--clarke-blue-light`, icon changes to a spinner. A progress bar (2px height, `--clarke-blue`) fills beneath the main content area.

### 4.6 Document Preview Panel

- Occupies the right 50% of the main content area (or full width on smaller viewports).
- Background: white card with standard card styling.
- The generated letter renders in a "paper" container: max-width 720px, centred, with subtle inset shadow (`inset 0 1px 4px rgba(0,0,0,0.04)`) to suggest a document page.
- Letter text: 16px body font, 1.7 line-height for reading comfort.
- Section headers within the letter: 17px, weight 600, `--clarke-blue`.
- Editable state: a thin `--clarke-gold` left border (3px) appears to signal "you can edit this." Clicking any paragraph activates inline editing with a subtle highlight background (`#FEFDF5`).

### 4.7 Navigation / Sidebar

- Fixed left sidebar, 260px wide.
- Background: sidebar gradient (see §1).
- Text: white at 90% opacity, weight 500. Active item: white at 100%, weight 600, with a left accent bar (3px, `--clarke-gold`) and a subtle background highlight (`rgba(255,255,255,0.08)`).
- Icons: 20px, outlined stroke style, white at 70% opacity (active: 100%).
- Bottom of sidebar: Clarke wordmark in white, 14px weight 700, with a small gold "S" shield icon reminiscent of the Superman emblem (simplified — a pentagon shape with the letter C inside, in `--clarke-gold`).

### 4.8 Loading / Progress States

- **Skeleton loaders** (not spinners) for content areas: animated shimmer gradient sweeping left-to-right over light grey rectangles matching the expected content shape. Shimmer uses `background-size: 200% 100%` with a `1.5s ease-in-out infinite` animation.
- **Progress bar** for pipeline stages (transcription → EHR retrieval → document generation): A horizontal bar with three segments, each filling in sequence with `--clarke-blue`. The current segment has a subtle pulse glow. Below the bar, a caption label names the active stage: "Transcribing audio…", "Retrieving patient context…", "Generating document…"

---

## 5. Animation and Transition Specifications

All animations serve one purpose: making Clarke feel premium, alive, and polished — especially in the demo video. No gratuitous motion.

| Animation | Trigger | Duration | Easing | Effect | Purpose |
|---|---|---|---|---|---|
| **Scroll entrance** | Element enters viewport | 500ms | `cubic-bezier(0.16, 1, 0.3, 1)` | Fade from opacity 0 + translateY(16px) to opacity 1 + translateY(0) | Content feels like it's gently rising into place. Premium feel. |
| **Button ripple-shine** | Click on primary button | 600ms total (400ms expand, 200ms fade) | expand: `ease-out`; fade: `ease-in` | White radial gradient from click origin to edges, then dissolve | Satisfying tactile feedback. Looks polished on video. |
| **Recording pulse** | Recording active | 2000ms, infinite | `ease-in-out` | Radial glow scales 1.0→1.3, opacity 0.4→0 | The product's heartbeat. Key visual moment in demo. |
| **Recording ring rotation** | Recording active | 3000ms, infinite, linear | `linear` | Conic gradient ring rotates 360° | Adds richness. Reads extremely well on video. |
| **Panel transition** | Tab/view change | 300ms | `cubic-bezier(0.16, 1, 0.3, 1)` | Outgoing panel fades out (150ms) + slides left 12px; incoming panel fades in (150ms) + slides from right 12px | Smooth, no jarring cuts. |
| **Document generation reveal** | Document ready | 800ms | `cubic-bezier(0.16, 1, 0.3, 1)` | Paper container scales from 0.97 to 1.0, opacity 0→1, slight upward drift (8px). Preceded by a 200ms "sparkle" flash of `--clarke-gold` glow on the document card border. | The "ta-da" moment. Most visually striking transition in the demo. |
| **Skeleton shimmer** | Content loading | 1500ms, infinite | `ease-in-out` | Left-to-right gradient sweep | Communicates progress. Feels modern. |
| **Progress bar fill** | Pipeline stage active | Variable (matches actual processing) | `ease-out` | Bar width interpolates from 0% to 100% per segment | Gives the user a sense of progress through the pipeline. |

### Cursor Behaviour

Cursors are a subtle but important part of perceived quality. The right cursor signals interactivity and reinforces the polished, premium feel.

| Context | Cursor | Notes |
|---|---|---|
| Default (body, text, backgrounds) | `default` | Standard arrow. |
| Clickable elements (buttons, links, cards, tabs, sidebar items) | `pointer` | The hand cursor. Every clickable element must show this — no exceptions. |
| Text inputs, editable fields, document edit mode | `text` | I-beam. Signals the area is editable. |
| Draggable elements (if any, e.g., panel resizers) | `grab` / `grabbing` | Open hand at rest, closed hand while dragging. |
| Disabled buttons, non-interactive elements | `not-allowed` | Reinforces that the element is inactive. |
| Loading/processing states (while waiting for AI pipeline) | `progress` | Signals the system is working. Use `progress` (spinner + arrow) rather than `wait` (hourglass) to indicate the user can still interact with other parts of the UI. |
| Hover over document preview text (non-editable) | `default` | Do NOT show `text` cursor on read-only document previews — it falsely suggests editability. |

---

## 6. Iconography and Visual Elements

### Icon Style

- **Library:** Lucide Icons (open-source, consistent, available in Gradio via HTML/SVG).
- **Style:** Outlined (stroke), not filled. Stroke weight 1.5px–2px.
- **Size:** 20px for navigation, 18px inline, 24px for feature icons.
- **Colour:** Inherits from context — `--clarke-text-secondary` by default, `--clarke-blue` when active, white on dark backgrounds.

### Clarke Logo Mark

A simplified shield shape (pentagon/crest) containing the letter "C" in a confident serif or semi-serif weight. Rendered in `--clarke-gold` on dark backgrounds, `--clarke-blue` on light backgrounds. Sized at 28px in the sidebar, 40px on the landing/welcome state. This is a subtle nod to the Superman emblem — enough to feel intentional, not enough to be derivative.

### Illustrative Elements

- **No illustrations or cartoons.** Clarke is a clinical tool.
- **Gradient orbs:** For empty states or welcome screens, use soft, semi-transparent gradient circles (peach-gold to lavender-blue, opacity 0.15–0.25) as decorative background elements — similar to the atmospheric quality in the Sarvam AI landing page. These add warmth without clutter.

---

## 7. Emotional Design Principles

Five principles that guide every visual decision. When in doubt, consult these.

### Principle 1: "Help Has Arrived"

Clarke should feel like relief — like the moment a colleague walks in and says "I've got this."  
**This means:** warm background gradients, welcoming empty states with clear next-step CTAs, a calm and confident colour palette.  
**This does NOT mean:** aggressive onboarding, dense dashboards that overwhelm on first load, or cold clinical sterility.

### Principle 2: "You Can Trust This"

Clinicians stake patient safety on Clarke's output. The design must project reliability.  
**This means:** consistent component styling, clear status indicators (you always know what state the system is in), legible text, no ambiguous icons, structured document previews that look like real clinical letters.  
**This does NOT mean:** excessive "trust badges" or security theatre. Trust is communicated through quality and consistency, not logos.

### Principle 3: "This Was Made for You"

The design should feel purpose-built for clinical work — not a repurposed generic SaaS template.  
**This means:** typography and spacing optimised for fatigued readers, clinical terminology used confidently (not dumbed down), the document preview mimics a real letter format, the workflow matches how clinicians actually conduct consultations.  
**This does NOT mean:** medical clip-art, stethoscope icons everywhere, or green-and-white "hospital" aesthetics.

### Principle 4: "Nothing Here Will Waste Your Time"

Every pixel earns its place. Every interaction has a purpose.  
**This means:** no decorative-only elements in the main workflow, progressive disclosure over information overload, clear visual hierarchy so the eye knows where to go, generous spacing that aids scanning.  
**This does NOT mean:** a stripped-down "developer" aesthetic. Polish is not waste — the ripple-shine, the recording pulse, the document reveal animation all serve the perception of quality.

### Principle 5: "Light, Not Heavy"

The emotional tone is warm, open, and optimistic — not clinical, corporate, or techy.  
**This means:** warm gradient backgrounds (peach → lavender), gold accents over grey, white space over density, rounded corners (12–16px) over sharp edges, the feeling of a sunlit room.  
**This does NOT mean:** pastel overload, childish roundness, or sacrificing information density where clinicians genuinely need it (e.g., the patient context panel can be data-rich — just well-structured).

---

## 8. Demo Video Optimisation

The 3-minute video is 30% of the judging score. These guidelines ensure the UI reads clearly on compressed video at typical viewing sizes (YouTube embed, ~720p effective resolution on a Kaggle page).

### Text Size for Video

- **Minimum text shown during video:** 16px (body) and above. Nothing smaller should be on-screen during a screen recording. If captions or metadata are 13–14px in the live UI, zoom the browser to 125% before recording.
- **Key numbers/metrics:** Render them at 24px+ so they're instantly legible in the video. E.g., "15 minutes saved per patient" on the results screen.

### Contrast Requirements

- All text on gradients must hit WCAG AA (4.5:1 ratio minimum). The hero gradient is light — use `--clarke-text-primary` (#1A1A2E) for headings on it, never grey.
- Status badges must be legible on white card backgrounds — the coloured backgrounds + dark text combinations in §4.3 are pre-tested for this.

### Hero Visual Moments (Optimise These for Video)

1. **The gradient landing/welcome screen.** First 5 seconds of the video. The warm peach → cool blue gradient with the Clarke logo. This is the first impression judges see — it must look stunning.
2. **The recording pulse animation.** Show this for at least 3–4 seconds in the video. The pulsing gold glow + rotating ring is the most "alive" visual element and communicates Clarke's core action.
3. **The document generation reveal.** The moment the "Processing…" state transitions to the rendered letter. The gold sparkle flash + the paper sliding into view should be given a beat in the video — pause narration slightly to let judges see it.
4. **The side-by-side comparison.** If shown: a split screen of "transcript-only letter" vs "Clarke's context-enriched letter" — use clear visual differentiation (left card grey border, right card gold border with a "★ Context-Enriched" badge).

### Colour on Camera

- Avoid pure white (#FFFFFF) backgrounds filling the entire screen — they blow out on video. The gradient backgrounds and the off-white `--clarke-bg-primary` (#FAFBFD) solve this.
- The blue-gold-white palette has excellent screen contrast range. Avoid the red except for alert states — red can bleed on compressed video.

---

## 9. Reference Mood Board Synthesis

### From the Superman Posters

**Take:** The colour palette — deep suit blue for trust/authority, warm emblem gold for warmth/value, cape red for alerts only, backlighting white for openness. The emotional register — confidence, hope, the arrival of help. The golden-hour atmosphere — warm light emanating from behind, suggesting dawn or relief.  
**Leave behind:** The dramatic intensity, the dark shadows, the movie-poster boldness. Clarke is warm and calm, not epic and intense.

### From Sarvam AI

**Take:** The gradient atmosphere — warm orange/peach flowing into cool lavender/blue, creating an ethereal, almost sunrise-like quality. The generous white space and uncluttered layout. The typographic confidence — bold, large, highly readable headings with strong weight differentiation. The pill-shaped buttons and rounded card corners.  
**Leave behind:** The serif font choice (Inter is more medical-appropriate than a display serif). The specific orange hue (Clarke shifts warmer toward gold to align with the Superman palette).

### Clarke's Unique Synthesis

Clarke blends Superman's emotional confidence and colour DNA with Sarvam AI's spatial grace and typographic clarity. The result: a healthcare interface that feels warm, trustworthy, and carefully made — like a product designed by someone who understands both the technology and the human on the other side of the screen. The warm peach-to-lavender gradients suggest dawn (a new day, help arriving), the gold accents suggest value (your time matters), and the deep blue grounds everything in clinical authority. When a tired NHS doctor opens Clarke at the end of a 12-hour shift, they should feel — even if only subconsciously — that someone built this with care for them.

---

*This document is the visual authority for all Clarke UI work. Every colour, font size, spacing value, and animation in the codebase must trace back to a specification defined here. When in doubt, re-read the five emotional design principles in §7.*
