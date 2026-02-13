# Clarke — PRD Implementation (Build Sequencing Plan)

**Version:** 1.0 | **Date:** 13 February 2026 | **Author:** Project Lead  
**Status:** Final  
**Parent document:** clarke_PRD_masterplan.md  
**Scope:** Build phases, sequencing, dependencies, time allocation, milestones, fallback paths  
**Not in scope:** Strategic rationale (masterplan.md), visual design (design_guidelines.md), user journey (userflow.md), architecture details (technical_spec.md), granular tasks (tasks.md), agent rules (rules.md)

---

## 1. Major Build Phases

The 24 working hours are divided into **5 phases** plus a protected submission-prep block. Each phase has a single clear deliverable that can be verified before moving on.

| Phase | Name | Hours | Deliverable |
|---|---|---|---|
| **0** | Environment & Data Foundation | 1–3 (3h) | Running GPU environment + FHIR server with 50 synthetic patients + demo audio files staged |
| **1** | Core Model Pipelines | 4–8 (5h) | MedASR transcription pipeline + MedGemma 4B EHR agent + orchestrator connecting them |
| **2** | Document Generation & End-to-End Pipeline | 9–12 (4h) | MedGemma 27B loaded + baseline letter generation + full pipeline wired (audio → transcript → context → letter) |
| **3** | UI Build & Integration | 13–16 (4h) | Functional Gradio UI connected to backend; complete end-to-end demo working in browser |
| **4** | Fine-tuning, Evaluation & Polish | 17–21 (5h) | LoRA fine-tuning (if feasible), quantitative evaluations, UI polish, demo audio verification |
| **5** | Deployment & Submission Prep | 22–24 (3h) | Public HF Space live, public GitHub repo, public LoRA adapter (if trained), README, submission checklist |

**Total: 24 hours.** Buffer week (Mon 16 – Sun 22 Feb) absorbs any slippage or provides time for writeup, video, and submission.

---

## 2. Dependency Graph

```
Phase 0: Environment & Data Foundation
   │
   ├──► Phase 1a: MedASR Pipeline (no dependency on FHIR)
   │
   ├──► Phase 1b: MedGemma 4B EHR Agent (depends on FHIR server from Phase 0)
   │         │
   │         ▼
   │    Phase 1c: Orchestrator (depends on 1a + 1b)
   │
   └──► Phase 2: Document Generation (depends on 1c — needs transcript + context to generate)
            │
            ▼
        Phase 3: UI Build & Integration (depends on Phase 2 — needs working backend)
            │
            ▼
        Phase 4: Fine-tuning + Evaluation + Polish (depends on Phase 3 — core must work first)
            │
            ▼
        Phase 5: Deployment & Submission Prep (depends on Phase 4 — deploy what's been built)
```

**Critical path:** Phase 0 → Phase 1b → Phase 1c → Phase 2 → Phase 3 → Phase 5. This is the minimum sequential chain that determines total build time. Minimum critical-path duration: ~19 hours (leaving 5 hours of float for Phase 4 evaluation/polish work, some of which can parallelise).

**Parallelisable work:**
- Phase 1a (MedASR) and Phase 1b (EHR Agent) are independent of each other and can overlap if two work streams are available. In practice, with a solo developer + AI agent, these are executed sequentially but either can go first.
- Synthetic training data generation (Phase 4) can begin during Phase 3 UI work if the developer kicks off a Claude API batch job in the background.

---

## 3. Hour-by-Hour Time Allocation

### PHASE 0 — Environment & Data Foundation (Hours 1–3)

| Hour | What Is Being Built | Tools | Deliverable | Done When |
|---|---|---|---|---|
| 1 | **GPU environment setup.** Provision HF Space with A100 40GB. Install Python 3.11, PyTorch 2.4.x, transformers, FastAPI, Gradio 5.x, bitsandbytes. Clone starter repo structure. | HF Spaces Docker, pip, git | Running Space with GPU confirmed | `torch.cuda.is_available() == True`, all core packages import |
| 2 | **FHIR server + synthetic data.** Deploy HAPI FHIR server (Docker container). Generate 50 UK-style synthetic patients using Synthea. Load into FHIR server. Verify REST access. | Synthea v3.3, HAPI FHIR v7.4, curl/requests | 50 patients queryable via FHIR API | `GET /fhir/Patient?_count=50` returns 50 patients with UK names, NHS numbers, mmol/L units |
| 3 | **Demo assets + project scaffolding.** Create project directory structure. Stage 3 pre-recorded demo audio clips (Mrs Thompson diabetes, Mr Okafor chest pain, Ms Patel asthma). Each ~60–90s, 16kHz WAV. Set up FastAPI app skeleton with placeholder endpoints. | ffmpeg, file management, FastAPI | Project structure + demo audio files + running FastAPI skeleton | FastAPI starts, `/health` returns 200, 3 WAV files play correctly |

**Uncertain assumption:** Synthea UK customisation may take longer than expected (NHS numbers, UK drug names, mmol/L units). **Contingency:** If Synthea UK config exceeds 1 hour, use default Synthea output and manually patch 5 key demo patients with UK-style data via direct FHIR PUT calls. The remaining 45 patients can be generic — judges will only see the 3–5 demo patients.

### PHASE 1 — Core Model Pipelines (Hours 4–8)

| Hour | What Is Being Built | Tools | Deliverable | Done When |
|---|---|---|---|---|
| 4 | **MedASR loading + audio ingestion.** Load `google/medasr` via transformers. Build audio ingestion: browser MediaRecorder API → WebSocket → server-side WAV conversion (16kHz, mono). | transformers, librosa, pydub, ffmpeg, websockets | Audio capture → valid WAV on server | Record 30s in browser → receive valid 16kHz WAV on server |
| 5 | **MedASR transcription pipeline.** Implement chunked transcription (`chunk_length_s=20`, `stride_length_s=2`, `return_timestamps=True`). Build WebSocket return of real-time transcript to frontend. Test with demo audio. | transformers pipeline, torch | Working audio → text pipeline | Transcribe 60s demo WAV, output is readable medical text with <10% WER on visual inspection |
| 6 | **MedGemma 4B EHR Agent — model + tools.** Load `google/medgemma-1.5-4b-it` in 4-bit quantised mode. Implement FHIR tool functions: `search_patients`, `get_conditions`, `get_medications`, `get_observations`, `get_allergies`, `get_diagnostic_reports`. Wire as LangGraph ReAct agent (or deterministic fallback — see §7). | transformers, bitsandbytes, langgraph, httpx | Agent loads, tools callable | Agent called with patient ID → returns raw FHIR resources as JSON |
| 7 | **MedGemma 4B context synthesis.** Add structured output: agent extracts facts from raw FHIR resources into standardised JSON schema (demographics, problem_list, medications, allergies, recent_labs, recent_imaging, last_letter_excerpt). Add clinical flags (rising trends, critical values). | Custom JSON schema, langgraph state | Structured patient context JSON | Agent returns well-formed context JSON for 3 demo patients; manual inspection confirms accuracy against FHIR data |
| 8 | **Orchestrator: connect MedASR + EHR Agent.** Build FastAPI endpoints: `POST /start-consultation` (activates audio + triggers EHR agent), `POST /end-consultation` (stops audio, combines transcript + context), `GET /patient-context/{id}`. Design document-generation prompt template (Jinja2): system message + transcript + context JSON + format specification. Test with mock data. | FastAPI, asyncio, Jinja2 | Working orchestrator producing combined prompt | Call `/start-consultation` with patient ID → context loads → call `/end-consultation` → combined prompt printed with correct structure |

**🔴 INTEGRATION TEST POINT 1 (end of Hour 8):** Run the Mrs Thompson demo scenario end-to-end through the backend (no UI yet). Audio file → MedASR → transcript. Patient ID → EHR Agent → context JSON. Combined prompt → print to console. Verify the combined prompt contains both the transcript text and the FHIR-sourced lab values. This is the critical fusion point — if it doesn't work here, everything downstream breaks.

**Uncertain assumption:** MedGemma 4B instruction-following for tool-calling. **Contingency:** See §7 (Fallback Paths).

### PHASE 2 — Document Generation & End-to-End Pipeline (Hours 9–12)

| Hour | What Is Being Built | Tools | Deliverable | Done When |
|---|---|---|---|---|
| 9 | **MedGemma 27B loading + baseline generation.** Load `google/medgemma-27b-text-it` in 4-bit NF4 quantisation (bitsandbytes, compute_dtype=bfloat16). Generate 3 baseline clinic letters using the combined prompts from Hour 8 (one per demo patient). | transformers, bitsandbytes, accelerate | MedGemma 27B loaded and generating text | 3 generated letters saved. Model produces coherent medical text (even if not yet NHS-formatted) |
| 10 | **Prompt engineering for NHS letter quality.** Iterate on the document-generation prompt: add explicit NHS letter structure instructions, exemplar letter fragments, positive/negative finding conventions. Regenerate 3 letters. Compare to baselines. Select best prompt. | Jinja2 templates, manual iteration | Optimised prompt template producing well-structured letters | 3 regenerated letters visually conform to NHS clinic letter format (date, addressee, history, investigations, plan) |
| 11 | **Wire end-to-end pipeline.** Connect `/end-consultation` endpoint to MedGemma 27B inference. Output: structured letter returned as JSON with sections (header, history, investigations, assessment, plan, medications, sign-off). Add latency logging. | FastAPI, torch inference | Complete backend pipeline | Call `/end-consultation` → receive generated letter JSON within 60 seconds |
| 12 | **Pipeline hardening.** Add error handling: timeout (120s max), OOM recovery (reduce context, retry), empty transcript handling, FHIR failure graceful degradation (generate from transcript only). Test 3 error scenarios intentionally. | Python exception handling, asyncio timeouts | Robust pipeline with graceful failures | Intentionally trigger empty audio, FHIR timeout, and oversized context — all handled with informative error messages, no crashes |

**Uncertain assumption:** MedGemma 27B fits in A100 40GB at 4-bit. **Contingency:** See §7 (Fallback Paths).

### PHASE 3 — UI Build & Integration (Hours 13–16)

| Hour | What Is Being Built | Tools | Deliverable | Done When |
|---|---|---|---|---|
| 13 | **Gradio UI — core layout.** Build main interface: left panel (patient context), centre panel (document display/editor), top bar (recording controls, status). Patient list dropdown. "Start Consultation" / "End Consultation" buttons. Recording indicator. Live transcript expandable section. | Gradio 5.x, custom CSS (NHS colours: #003087, #005EB8, #FFFFFF) | UI renders with all panels and controls | UI loads in browser. All buttons clickable. Panels correctly positioned at 1920×1080 |
| 14 | **Gradio UI — data binding.** Connect UI to backend: patient selection triggers EHR agent → context panel populates. "Start" activates audio capture (JavaScript interop). "End" triggers document generation → letter appears. Inline editing of letter text. "Sign Off" button. Export: copy to clipboard. | Gradio event handlers, gr.State, JavaScript interop | Fully interactive UI connected to backend | Select patient → context loads → start recording → stop → letter appears → edit a line → sign off. All stages work |
| 15 | **End-to-end integration testing (3 demo scenarios).** Test Mrs Thompson (diabetes), Mr Okafor (chest pain), Ms Patel (asthma) — complete flow using pre-recorded audio. Verify: correct transcription, accurate context, clinically coherent letters, working editing, successful sign-off. | Pre-recorded WAV files, manual verification | 3 passing end-to-end scenarios | All 3 scenarios complete without crash. Generated letters are clinically appropriate for each patient |
| 16 | **Bug fixing + UX tightening.** Fix all issues from Hour 15. Add loading spinners, progress indicators ("Transcribing... → Retrieving context... → Drafting letter..."), error toast messages. Ensure UI doesn't freeze during model inference. | Gradio UI components, CSS | Stable, responsive application | Re-run all 3 scenarios. No UI freezes, no uncaught errors, loading states visible |

**🔴 INTEGRATION TEST POINT 2 (end of Hour 16):** Full demo dry-run. Record screen while running the Mrs Thompson scenario exactly as it would appear in the competition video. Watch the recording. Verify: the flow is smooth, the letter is good, no glitches. This recording can serve as a rough-cut backup video if time runs out later.

### PHASE 4 — Fine-tuning, Evaluation & Polish (Hours 17–21)

| Hour | What Is Being Built | Tools | Deliverable | Done When |
|---|---|---|---|---|
| 17 | **Synthetic training data generation.** Generate 250 training triplets (transcript, FHIR context JSON, reference NHS letter) using Claude API. Each based on a unique clinical scenario. Manually review 20 for quality. Split: 200 train, 50 test. | anthropic SDK, custom scripts | 250 triplets in train.jsonl + test.jsonl | Files pass schema validation. 20 reviewed samples are clinically plausible and correctly formatted |
| 18 | **LoRA fine-tuning MedGemma 27B.** QLoRA: 4-bit NF4 base, LoRA on attention + MLP layers. rank=16, alpha=32, lr=2e-4, epochs=3, batch=2, grad_accum=8. Monitor training loss. | peft, trl (SFTTrainer), bitsandbytes, wandb | Saved LoRA adapter | Training completes without OOM. Final loss < initial loss. Adapter <500MB |
| 19 | **Post-training evaluation.** Generate 50 test letters with fine-tuned model. Compute BLEU, ROUGE-L vs held-out references. Compare to 3 baseline letters from Hour 9. Manual review of 10 letters for NHS format compliance, clinical accuracy, correct use of FHIR values. | evaluate (HF), rouge_score, sacrebleu | Evaluation report | Fine-tuned scores > baseline scores. Report saved as evaluation_report.md |
| 20 | **MedASR + EHR Agent evaluation.** MedASR: compute WER on 20 dictation + 10 ambient clips using jiwer; compare to Whisper large-v3. EHR Agent: test fact recall/precision/hallucination on 20 patients vs gold standards. | jiwer, openai-whisper, custom eval scripts | WER comparison table + agent accuracy report | All metrics computed. Results appended to evaluation_report.md |
| 21 | **UI polish + demo prep.** NHS Design System aesthetics (colours, typography, spacing). Loading animations. Verify 3 demo audio clips transcribe cleanly. Screen-record a polished demo dry-run. | CSS, Gradio theming, screen recording | Production-quality UI + demo recording | UI looks professional. Demo dry-run recording is smooth |

**Decision gate (end of Hour 18):** If LoRA training fails (OOM, loss diverges, takes >2 hours), abandon fine-tuning. Use base MedGemma 27B with the optimised prompt from Hour 10. Redirect Hours 19–20 to additional prompt engineering, evaluation of the base model, and extra UI polish. Document the fine-tuning plan in the writeup as "production roadmap" rather than "completed."

**Uncertain assumption:** LoRA fine-tuning fits in remaining A100 VRAM alongside loaded models. **Contingency:** Unload all other models during training (MedASR + MedGemma 4B). Reload after training completes. If still OOM: reduce rank to 8, reduce max_seq_length to 2048, reduce dataset to 100 examples.

### PHASE 5 — Deployment & Submission Prep (Hours 22–24)

| Hour | What Is Being Built | Tools | Deliverable | Done When |
|---|---|---|---|---|
| 22 | **HF Space deployment.** Push complete application to public HF Space. Upload LoRA adapter (if trained) to HF Hub as separate model repo tracing to `google/medgemma-27b-text-it`. Verify public access from incognito browser. | HF Spaces CLI, huggingface_hub SDK, git-lfs | Live public demo + public model repo | External browser (incognito) can access demo, select patient, play audio, receive letter |
| 23 | **GitHub repo + README.** Push clean code to public GitHub repo. Write README: project description, architecture diagram (ASCII or image), installation instructions, evaluation results, model card, licence (Apache 2.0 code, HAI-DEF terms for models). Add docstrings to all .py files. | git, markdown | Documented public GitHub repo | README has architecture diagram, quickstart, eval table, licence. All .py files have docstrings |
| 24 | **Final verification + submission checklist.** End-to-end smoke test of live demo. Verify all 3 public artefacts: GitHub repo, HF Space, HF model repo (if applicable). Create `submission_checklist.md`. | Manual testing | All artefacts publicly accessible | GitHub ✓, HF Space ✓, HF model repo ✓, demo runs error-free from external device |

---

## 4. Integration Points and Their Order

Clarke has 5 components. They are wired together in this order, with rationale:

| Order | Integration | Why This Order |
|---|---|---|
| 1st | **FHIR Server ↔ EHR Agent** (Hour 6–7) | The EHR Agent is useless without data to query. FHIR server must be up first. This is also the riskiest integration (MedGemma 4B tool-calling bugs), so we tackle it early to allow time for fallback. |
| 2nd | **MedASR ↔ Orchestrator** (Hour 8) | MedASR is the most straightforward model (audio → text). Connecting it to the orchestrator is low-risk and gives us the transcript half of the fusion point. |
| 3rd | **Orchestrator ↔ MedGemma 27B** (Hour 11) | This completes the backend pipeline. We need both transcript and context available before connecting the document generator. |
| 4th | **Gradio UI ↔ Backend** (Hour 14) | UI is the last layer. Building it before the backend is stable wastes time on broken bindings. |
| 5th | **LoRA Adapter ↔ MedGemma 27B** (Hour 18–19) | Fine-tuning is an improvement on top of a working pipeline, not a prerequisite. If it fails, the pipeline still works with the base model. |

**Minimal viable integration (rough end-to-end demo):** Achieved at end of Hour 11 — backend pipeline produces a letter from audio + patient ID, viewable in terminal. No UI yet, but the core pipeline works.

---

## 5. Day-End Checkpoints

### End of Day 1 — Hour 8 (Friday 13 Feb)

All of the following must be true:

1. ✅ HF Space is running with GPU confirmed.
2. ✅ HAPI FHIR server has 50 synthetic patients loaded and queryable.
3. ✅ MedASR transcribes a demo WAV file and returns readable medical text via the `/transcribe` endpoint or equivalent.
4. ✅ MedGemma 4B EHR Agent returns a structured context JSON for at least 3 demo patients when given a patient ID.
5. ✅ The orchestrator combines a transcript and context JSON into a correctly structured document-generation prompt.
6. ✅ Integration Test Point 1 has passed (Mrs Thompson scenario: combined prompt contains both transcript text AND FHIR-sourced lab values).

**If behind:** If MedGemma 4B agent is not working as a LangGraph tool-caller, trigger Fallback Path #2 (§7) immediately — do not spend Day 2 debugging it.

### End of Day 2 — Hour 16 (Saturday 14 Feb)

All of the following must be true:

1. ✅ MedGemma 27B is loaded and generates coherent clinic letters from combined prompts.
2. ✅ The complete backend pipeline works: audio → transcript → context → letter, invokable via API.
3. ✅ The Gradio UI is functional: patient selection, recording, context display, letter display, inline editing, sign-off.
4. ✅ All 3 demo scenarios (Thompson, Okafor, Patel) run end-to-end in the browser without crashing.
5. ✅ Integration Test Point 2 has passed (screen-recorded demo dry-run of Mrs Thompson scenario is smooth).
6. ✅ Generated letters include both conversation content AND FHIR-sourced data (the core Clarke differentiator).

**If behind:** At this point, assess the must-have list (masterplan §12). If ≥2 must-haves are incomplete, cancel ALL nice-to-haves (fine-tuning, quantitative evaluation, ward round mode, PDF export). Spend all of Day 3 completing the core pipeline + deployment.

### End of Day 3 — Hour 24 (Sunday 15 Feb)

All of the following must be true:

1. ✅ Public HF Space is live and accessible from any browser.
2. ✅ Public GitHub repo with clean code, README with architecture diagram, and docstrings.
3. ✅ At least 3 demo scenarios work flawlessly on the live HF Space.
4. ✅ Submission checklist confirms all competition requirements are met (except video and writeup, which are scheduled for buffer week).

**Nice-to-haves completed (if on schedule):**
- LoRA adapter trained and published on HF Hub.
- WER comparison table (MedASR vs Whisper).
- EHR Agent fact recall/precision metrics.
- BLEU/ROUGE-L evaluation of document generation.
- evaluation_report.md with all quantitative results.

---

## 6. Minimum Viable Demo (MVD)

### Protected Core (must be done in first 24 hours)

These elements are the irreducible core of Clarke's competition story:

1. **MedASR transcription** — audio in, medical transcript out.
2. **MedGemma 4B context retrieval** — patient ID in, structured FHIR context out (even if via deterministic FHIR queries + MedGemma summarisation rather than full agentic tool-calling).
3. **MedGemma 27B document generation** — transcript + context in, NHS-format letter out (even with base model, no fine-tuning).
4. **End-to-end orchestration** — all three stages connected, single user action triggers the full pipeline.
5. **Functional Gradio UI** — patient selection, recording, context panel, letter display, basic editing, sign-off.
6. **3 demo scenarios working** — pre-recorded audio, verified output.
7. **Public HF Space** — live, accessible.
8. **Public GitHub repo** — README, licence.

### Can Safely Slip to Buffer Week (Mon 16 – Sun 22 Feb)

- LoRA fine-tuning + adapter publication
- All quantitative evaluations (WER, BLEU, ROUGE-L, fact recall)
- Ward Round mode
- PDF export
- Discrepancy flagging (allergy mismatch alerts)
- NHS Design System visual polish (accessibility scores)
- Video recording and editing
- Writeup drafting

### Absolute Floor (if catastrophic failure)

If a critical component fails entirely (e.g., MedGemma 27B cannot be deployed on any available hardware):

- **MedASR transcription** works and is demoed.
- **MedGemma 4B EHR context retrieval** works and is demoed.
- **Document generation** uses MedGemma 4B with heavy prompt engineering as a fallback (reduced quality, but functional).
- **The story is still told:** three HAI-DEF models in a pipeline, even if one is degraded. The video focuses on the vision and the two working components.

---

## 7. Fallback Paths for Known Risks

### Risk 1: MedGemma 27B deployment fails (OOM, quota rejection, >60s inference)

- **Trigger:** Model fails to load in 4-bit NF4 on A100 40GB, or inference exceeds 120 seconds.
- **Fallback A:** GGUF Q8_0 quantisation via Ollama (31.8GB). Switch inference to Ollama API calls. Impact on build: +1 hour to set up Ollama within Docker, swap inference code. Schedule: borrow from Phase 4 (cut evaluation time).
- **Fallback B:** If Ollama also fails — use MedGemma 4B (`google/medgemma-1.5-4b-it`) for document generation with extensively engineered prompts. Quality will be lower but the pipeline remains functional. Mention 27B as the "production configuration" in writeup.
- **Impact on remaining sequence:** If Fallback B is triggered, skip LoRA fine-tuning entirely. Redirect all Phase 4 time to prompt engineering and evaluation of the 4B-based generation.

### Risk 2: MedGemma 4B instruction-following bugs (system prompt leaks, meta-commentary)

- **Trigger:** MedGemma 4B fails to reliably call FHIR tools via LangGraph, or outputs contain training artifacts / system prompt leaks after 2 hours of prompt engineering (i.e., by end of Hour 7).
- **Fallback:** Abandon LangGraph agentic tool-calling. Instead, use **deterministic FHIR queries** (hardcoded Python functions that query FHIR endpoints for the standard resource set: Conditions, Medications, Observations, Allergies, DiagnosticReports). Pass the raw FHIR JSON to MedGemma 4B for **summarisation only** (not tool-calling). The output is the same structured context JSON; the agent just doesn't autonomously decide which queries to run.
- **Impact on narrative:** We can still describe this as "MedGemma 4B acting as an EHR understanding agent" — the model is still processing FHIR data and generating structured summaries. The agentic workflow story is slightly weaker but still holds because the three-model pipeline is intact.
- **Impact on remaining sequence:** Saves time (deterministic queries are faster to implement than debugging LangGraph). No downstream changes needed.

### Risk 3: Time overrun — 24 hours is insufficient

- **Trigger:** End of Day 2 checkpoint shows ≥2 must-haves incomplete.
- **Fallback:** Cancel all nice-to-haves (masterplan §12, items 11–20). Day 3 is entirely dedicated to completing the core pipeline and deployment. Fine-tuning, quantitative evaluation, Ward Round mode, and PDF export are deferred to buffer week or dropped entirely.
- **Impact on remaining sequence:** Day 3 becomes: finish pipeline → finish UI → deploy → smoke test. No evaluation, no polish. Buffer week picks up the rest.

### Risk 4: MedASR ambient performance is unacceptable (WER >15% on demo audio)

- **Trigger:** Demo audio clips produce incoherent transcripts after basic prompt/config tuning.
- **Fallback:** Switch to **dictation-style demo audio** — the clinician dictates a consultation summary post-visit rather than ambient two-party capture. MedASR was trained on dictation, so this is its strong suit. The demo still shows MedASR in action; the writeup acknowledges ambient capture as a production fine-tuning target.
- **Impact on remaining sequence:** None — just swap the audio files. The rest of the pipeline is identical.

### Risk 5: HAPI FHIR server fails within HF Spaces Docker

- **Trigger:** FHIR server won't start, or startup takes >15 minutes, or conflicts with GPU container.
- **Fallback:** Replace HAPI FHIR with a **mock FHIR API** — a set of FastAPI endpoints that return pre-loaded Synthea JSON files. The demo UX is identical (the EHR Agent still makes HTTP calls to a FHIR-like API). Implement in ~30 minutes.
- **Impact on remaining sequence:** Minimal. The mock API is simpler and faster.

---

## 8. Integration Testing Strategy

Two mandatory integration test points are built into the schedule. A third is recommended.

### Integration Test Point 1 — End of Hour 8 (End of Day 1)

**What:** Backend-only end-to-end test. Run the Mrs Thompson scenario through the entire backend pipeline without any UI.

**How:**
1. Feed `demo_data/mrs_thompson.wav` to MedASR → capture transcript.
2. Feed patient ID to EHR Agent → capture context JSON.
3. Combine into document-generation prompt → print to console.
4. Verify the combined prompt contains: (a) transcript text mentioning HbA1c, fatigue, gliclazide; (b) FHIR-sourced values: HbA1c 55 mmol/mol, eGFR 52, Penicillin allergy.

**Pass criteria:** The fusion point works — the prompt contains both conversation content and record data. If this fails, Day 2 cannot proceed as planned.

### Integration Test Point 2 — End of Hour 16 (End of Day 2)

**What:** Full UI end-to-end test. Screen-record a complete demo run of the Mrs Thompson scenario exactly as it would appear in the competition video.

**How:**
1. Open Clarke in browser.
2. Select Mrs Thompson from patient list.
3. Verify context panel populates with correct data.
4. Click "Start Consultation," play pre-recorded audio.
5. Click "End Consultation."
6. Verify draft letter appears within 60 seconds.
7. Verify letter contains FHIR-sourced lab values.
8. Edit one line, click "Sign Off."
9. Watch screen recording for any glitches.

**Pass criteria:** The recording is a viable rough-cut demo video. If it's not smooth, Day 3 prioritises bug-fixing over polish.

### Integration Test Point 3 (Recommended) — Hour 22 (Post-deployment)

**What:** External access test. Load the live HF Space from a different device/browser (incognito) and run one demo scenario.

**Pass criteria:** An external user can access the demo, select a patient, and receive a generated letter. No authentication barriers, no CORS errors, no missing assets.

---

## 9. Polish and Submission Prep Allocation

### Protected time within the 24-hour build:

| Activity | Allocated Hours | When |
|---|---|---|
| UI visual polish (NHS colours, typography, loading states) | 1h | Hour 21 |
| HF Space deployment + verification | 1h | Hour 22 |
| GitHub repo + README documentation | 1h | Hour 23 |
| Final smoke test + submission checklist | 1h | Hour 24 |
| **Total protected:** | **4h** | Hours 21–24 |

### Buffer week allocation (Mon 16 – Sun 22 Feb):

**Monday 16 February — Writeup Day**

Complete the 3-page writeup for the competition submission. The writeup should use the required Kaggle Writeup template (Project name, Your team, Problem statement, Overall solution, Technical details). It must completely satisfy and exceed every judging criterion to maximise chance of winning. Keep it as high-level and easy-to-read as possible — the host explicitly said "less is more" and to let the video carry most of the conceptual weight. Target ~1,000–1,200 words of text (leaving room for images/diagrams within the ~1,500 word / 3-page limit). Any deferred nice-to-haves (quantitative evaluations, additional code cleanup) that strengthen the writeup should be completed on this day as well.

**Tuesday 17 February – Saturday 21 February — Video Production (5 days)**

Complete the 3-minute video. The video is the primary, attention-grabbing medium of communication and carries the heaviest judging weight (Execution & Communication = 30%). It should be optimised to exceed every aspect of the judging criteria: compelling problem storytelling, clear demonstration of the three-model pipeline, visible FHIR-context enrichment in the generated letter, polished screen recordings, professional voiceover, and a cohesive narrative that ties together problem → solution → impact → technical feasibility. Allocate time across these 5 days for: scripting (Tue), screen capture of live demo (Wed), voiceover recording (Thu), editing and polish (Fri–Sat).

**Sunday 22 February — Submission Day**

Submit everything as a single Kaggle Writeup package:

1. 3-page writeup (finalised and submitted via Kaggle Writeups tab)
2. Video (3 minutes or less, linked in writeup)
3. Public code repository (GitHub link in writeup)
4. Public interactive live demo app (HF Space link in writeup)
5. Open-weight Hugging Face model tracing to a HAI-DEF model (HF Hub link in writeup, if LoRA adapter was trained)

Final verification checklist: all links are public and accessible from incognito browser, video plays without issues, HF Space demo runs end-to-end, GitHub repo has README + licence + docstrings.

**Hard rule:** Video and writeup are NOT attempted during the 24-hour build (Fri 13 – Sun 15 Feb). Those hours are 100% product engineering. The buffer week exists precisely for communication artefacts and submission preparation.

---

## Appendix: Phase-Risk Cross-Reference

| Phase | Primary Risk | Fallback Path | Decision Point |
|---|---|---|---|
| 0 | FHIR server setup fails | Mock FHIR API (Risk 5) | If not running by end of Hour 2 |
| 1 | MedGemma 4B tool-calling fails | Deterministic FHIR + summarisation (Risk 2) | If not working by end of Hour 7 |
| 2 | MedGemma 27B won't load/infer | Ollama GGUF or 4B fallback (Risk 1) | If not generating by end of Hour 9 |
| 3 | Time overrun | Cancel nice-to-haves (Risk 3) | Day 2 checkpoint (Hour 16) |
| 4 | LoRA training fails | Base model + prompt engineering | End of Hour 18 |
| 4 | MedASR WER too high | Dictation-style audio (Risk 4) | During Hour 20 evaluation |

---

*This document derives from clarke_PRD_masterplan.md. Every phase, checkpoint, and fallback is traceable to the goals, constraints, risks, and success criteria defined there.*
