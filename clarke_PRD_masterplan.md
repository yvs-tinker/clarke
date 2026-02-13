# Clarke — PRD Masterplan

**Version:** 1.0 | **Date:** 13 February 2026 | **Author:** Project Lead  
**Status:** Final — all other PRDs derive from this document  
**Competition:** MedGemma Impact Challenge (Kaggle)  
**Targets:** Main Track 1st Place ($30,000) + Agentic Workflow Prize ($5,000)

---

## 1. What Are We Building?

**One sentence:** Clarke is an open-source, privacy-preserving AI system that listens to a clinician–patient consultation, simultaneously retrieves the patient's electronic health record context, and generates a complete, structured NHS clinical document — ready for review and sign-off — using a pipeline of three HAI-DEF medical models (MedASR → MedGemma 4B → MedGemma 27B) running entirely within the hospital network.

**30-second pitch:** You talk to your patient. Clarke listens. In the background, it pulls the patient's history, medications, recent blood results, and imaging from the electronic health record. By the time you say goodbye, a draft clinic letter — structured to NHS standards, populated with actual investigation values, and chronologically ordered — is waiting on your screen. You review it, edit if needed, sign off. No dictaphone. No secretary. No 15-minute write-up from memory. No logging into five separate systems. Your letter is done before the next patient walks in. And no patient data ever leaves the building.

**Core architectural concept:** Clarke is a three-model agentic pipeline:

1. **MedASR** (105M params, `google/medasr`) — converts the consultation audio into a medical transcript.
2. **MedGemma 1.5 4B** (4B params, `google/medgemma-1.5-4b-it`) — acts as an autonomous EHR navigation agent, querying a FHIR server to retrieve and structure the patient's medical context.
3. **MedGemma 27B** (27B params, `google/medgemma-27b-text-it`) — receives both the transcript and the structured patient context as a single prompt, and generates a complete NHS-format clinical document.

The critical innovation is the **fusion point**: the document generator sees both the conversation and the record simultaneously. No existing product does this.

---

## 2. Who Are We Building It For?

**Primary target user:** NHS hospital doctors — specifically, consultants and registrars in outpatient clinics and junior doctors on inpatient ward rounds. These clinicians see 10–12 patients per half-day session and must produce a formal clinical letter (or ward round entry) for every encounter.

**Their clinical context:** These doctors work within the NHS, the UK's publicly funded health system, which employs ~190,200 FTE doctors in England alone [NHS Digital Workforce Statistics, August 2025; GP Workforce, December 2025]. They use fragmented EHR systems (EMIS, SystmOne, Cerner/Oracle Health) where patient data is siloed across multiple modules.

**Their daily pain points:**

- **Documentation consumes the majority of their day.** The TACT study (137 NHS doctors, 7 months observation) found doctors spend 73% of their time on non-patient-facing tasks, with only 17.9% on direct patient care [Arab et al., QJM 2025]. Our clinician survey (n=47, Jan–Feb 2026) confirmed documentation takes ~15 minutes per patient encounter.
- **Information retrieval is manual and slow.** To write a single clinic letter, a clinician must log into multiple systems to find lab results, imaging reports, medication lists, and the previous clinic letter. Ward round preparation takes 30–60 minutes for 10–12 patients.
- **The result is burnout and workforce attrition.** 61% of NHS trainees are at moderate or high risk of burnout [GMC NTS 2025]. 42% of medical staff report work-related stress [NHS Staff Survey 2024].

**Their workflow today (without Clarke):** Clinician sees the patient → opens 3–5 separate system modules to look up relevant history → conducts the consultation → opens a dictation app or word processor → writes the letter from memory → manually inserts lab values and medication lists → sends to secretary or submits directly → moves to next patient. Elapsed documentation time: ~15 minutes per encounter. Total documentation burden: 2.5–3 hours per clinic session.

---

## 3. Why Are We Building It?

**Problem statement:** NHS doctors spend four hours on administrative tasks for every one hour with patients. Clinical documentation — letters, discharge summaries, referral notes, ward round entries — consumes the largest share of that time. This documentation requires clinicians to assimilate information scattered across disconnected IT systems, compose structured narratives, and ensure accuracy under severe time pressure. The consequence is a workforce crisis: doctors burning out, patients waiting longer, and safety incidents caused by incomplete or fragmented records.

**Quantified magnitude:**

| Dimension | Value | Source |
|---|---|---|
| NHS doctors affected (England) | 190,200 FTE | NHS Digital Aug 2025 + GP Workforce Dec 2025 |
| Time on non-patient tasks | 73% of working day | Arab et al., QJM 2025 (TACT study) |
| Documentation time per encounter | ~15 minutes | MedGamma Clinician Survey, n=47 |
| Clinician-hours freed daily (at 30 min/doctor) | 95,100 hours/day | Calculated: 190,200 × 0.5h |
| Equivalent FTE doctors freed | ~11,888 | Calculated: 95,100h ÷ 8h/day |
| NHS medical vacancies (secondary care) | 7,248 | NHS Digital, Sep 2025 |
| Annual financial value of reclaimed time | £1.07 billion | Calculated: 190,200 × £5,642/yr |
| Burnout reduction from ambient AI (US evidence) | 51.9% → 38.8% at 30 days | Olson et al., JAMA Netw Open 2025 |
| NHS waiting list | 7.31 million cases | BMA/King's Fund, Nov 2025 |
| Outpatient consultations with missing key info | 15% | Burnett et al., BMC Health Serv Res 2011 |
| Annual NHS clinical negligence cost | £4.6 billion | NHS Resolution 2024/25 |

**Why existing solutions fail:**

- **Heidi Health / DAX Copilot / Abridge / Nabla / Tortus / Accurx:** All are ambient scribes that generate documents from conversation alone — none integrate EHR data. The output still requires manual enrichment with lab values, medication lists, and imaging results. All are cloud-dependent and closed-source, which creates data sovereignty concerns for the NHS. Heidi charges $99/month per clinician; at scale across the NHS, that's £226M/year.
- **Existing EHR systems (EMIS, SystmOne, Cerner):** Present data in silos. No synthesis, no summarisation, no document generation.
- **The specific gap Clarke fills:** An open-source, fully local system that fuses ambient documentation with intelligent EHR retrieval — producing context-enriched clinical documents without patient data leaving the hospital, at zero per-clinician cost. No existing product does both.

---

## 4. Why Is It Important?

If Clarke works as designed, the real-world impact is:

- **Time:** 30 minutes saved per clinician per day [Olson et al., JAMA Netw Open 2025] — equivalent to 11,888 additional FTE doctors across the NHS, exceeding the current 7,248 vacancy count.
- **Burnout:** A 13-percentage-point absolute reduction in burnout prevalence [Olson et al., 2025] and a 21-percentage-point reduction in documentation-specific burnout at 84 days [You et al., JAMA Netw Open 2025].
- **Patient safety:** Clarke cross-references conversation with record data — flagging discrepancies (e.g., clinician says "no allergies" but record shows penicillin allergy). 15% of NHS outpatient consultations involve missing key clinical information, with 20% of those resulting in documented risk of harm [Burnett et al., 2011].
- **Cost:** Zero licensing fees versus £226M/year for commercial alternatives at scale. One-time GPU hardware cost of £5k–£15k per trust.
- **Waiting list:** Every hour freed from documentation is an hour available for patient care — directly relevant to the 7.31M patient backlog.

**Honest caveats:** (1) The 30-minute daily saving comes from US ambulatory care studies, not NHS settings — NHS-specific validation is required. (2) Burnout figures are from self-selected US pilot cohorts with modest response rates. (3) The financial estimate assumes reclaimed time is used productively. (4) AI-generated documents will contain errors — mandatory clinician review is non-negotiable. These caveats are detailed in Clarke_Product_Specification_V2.md §5.2.

---

## 5. What Are the Goals?

### 5a. Competition Goals

- **Primary:** Win Main Track 1st Place ($30,000).
- **Secondary:** Win Agentic Workflow Prize ($5,000) — "the project that most effectively reimagines a complex workflow by deploying HAI-DEF models as intelligent agents or callable tools."

### 5b. Product Goals (What Clarke Must Demonstrate)

1. A working end-to-end pipeline: audio in → medical transcript → FHIR context retrieval → structured NHS clinical letter out.
2. Three HAI-DEF models operating as autonomous agents within a coordinated workflow.
3. Real-time (or near-real-time) operation: draft letter appears within 60 seconds of clicking "End Consultation."
4. Clinician-facing UI that is polished, intuitive, and demonstrates the complete user journey.
5. Quantitative evaluation showing HAI-DEF model superiority over general-purpose alternatives.

### 5c. Narrative Goals (Mapped to Judging Criteria)

| Criterion | Weight | What Clarke's Submission Must Demonstrate |
|---|---|---|
| **Effective use of HAI-DEF models** | 20% | Three HAI-DEF models used purposefully (not superficially). Each chosen over a general-purpose alternative with quantified justification (MedASR vs Whisper: 58–82% fewer errors). Pipeline creates emergent value no single model could achieve. LoRA fine-tuning on MedGemma 27B for NHS letter generation. Public LoRA adapter on HF Hub. |
| **Problem Domain** | 15% | Captivating story rooted in NHS workforce crisis with peer-reviewed evidence. Clear target user (NHS doctors). Quantified unmet need. Named competitors and why each falls short. |
| **Impact Potential** | 15% | Specific, sourced impact estimates (£1.07B, 11,888 FTE equivalent). Honest caveats clearly stated. Burnout reduction evidence from JAMA. |
| **Product Feasibility** | 20% | Working live demo on Hugging Face Spaces. Complete technical stack documented. Fine-tuning methodology specified. Performance evaluation (WER, BLEU, ROUGE-L, fact recall). Deployment challenges with specific mitigations. |
| **Execution & Communication** | 30% | Polished 3-minute video demonstrating full pipeline. Concise writeup (≤1,500 words) following the required template. Clean, annotated public GitHub repo. Public HF Space with live demo. Cohesive narrative across all materials. |

---

## 6. What Are the Constraints?

| Constraint | Detail |
|---|---|
| **Time** | 24 working hours (3 days × 8 hours: Fri 13 – Sun 15 Feb). |
| **Team** | Solo developer (with AI coding assistants: Claude Code / Codex). |
| **Writeup** | ≤3 pages (~1,500 words; ~1,000–1,200 with images). Kaggle Writeup format (not PDF). Must follow required template: Project name, Team, Problem statement, Overall solution, Technical details. |
| **Video** | ≤3 minutes. Must demonstrate the application and address judging criteria. |
| **HAI-DEF requirement** | Must use at least one HAI-DEF model. Clarke uses three (MedASR, MedGemma 4B, MedGemma 27B). |
| **Demo standard** | Judges evaluate as a demonstration application, not a production system [Yun Liu, competition discussion]. Regulatory pathway is not the focus. |
| **Special track** | One selection only. Targeting Agentic Workflow Prize. |
| **Submission format** | Kaggle Writeup (one per team, editable and re-submittable before deadline). |
| **Winner licence** | CC BY 4.0 for code/demos if selected as winner. HAI-DEF model weights remain under their own licence. |
| **GPU availability** | MedGemma 27B requires ~54GB VRAM unquantised. 4-bit NF4 quantisation fits on A100 40GB. Vertex AI A100 quota requests reportedly being rejected. Fallback: GGUF quantisation via Ollama (Q8_0 = 31.8GB). HF Spaces with A100 40GB is the primary deployment target. |
| **Data** | No dataset provided. All data must be sourced (Synthea synthetic patients) or generated (synthetic transcripts/letters via Claude API). Non-commercial datasets are permitted [Daniel Golden, competition forum]. |
| **Language** | Submissions must be in English. |
| **Team size cap** | Maximum 5 members. |

---

## 7. What Are the Non-Goals?

We are explicitly **not** building or pursuing the following:

1. **Production-grade security or HIPAA/GDPR compliance.** This is a demo. Judges have confirmed regulatory pathway is not the evaluation focus.
2. **Real patient data handling.** All demo data is synthetic (Synthea-generated). No consent, anonymisation, or IG approvals needed for the demo.
3. **EHR write-back.** Clarke generates documents for export (PDF, clipboard, FHIR DocumentReference) but does not write back into any EHR system. Write-back is a Phase 2 production feature.
4. **Multi-language support.** English only for the demo.
5. **Mobile deployment / Edge AI.** Clarke targets the Agentic Workflow Prize, not Edge AI. The demo runs on a GPU server, not on-device.
6. **Multi-trust deployment or scalability testing.** Demo uses a single HAPI FHIR server with 50 synthetic patients.
7. **Comprehensive MedASR accent adaptation.** If base MedASR WER is acceptable (<10%) on our demo audio, we document accent fine-tuning as a production requirement rather than implementing it within the 24-hour build.
8. **Ward Round mode (if time-constrained).** The clinic letter pipeline is the priority. Ward Round mode is a stretch goal for Day 3.

---

## 8. What Are the Key Risks and Mitigations?

| # | Risk | Severity | Mitigation / Fallback |
|---|---|---|---|
| 1 | **MedGemma 27B deployment fails** (OOM, quota rejection, >60s inference). Known issue: requires ~54GB VRAM; Vertex AI quotas being rejected. | Critical | Primary: 4-bit NF4 quantisation via bitsandbytes on A100 40GB (fits in ~16GB VRAM). Fallback 1: GGUF Q8_0 via Ollama (31.8GB). Fallback 2: Use MedGemma 4B with heavy prompt engineering for document generation (reduced quality but functional demo). |
| 2 | **MedGemma 4B instruction-following bugs** (leaks system prompts, generates meta-commentary, outputs training artifacts). Known issue from competitor reports. | High | Thorough prompt engineering with explicit output format constraints. Robust output parsing that strips meta-commentary and extracts structured JSON only. Testing with ≥5 patient scenarios before integration. If unusable as LangGraph agent: fall back to deterministic FHIR queries with MedGemma 4B used only for context summarisation (not tool-calling). |
| 3 | **Time overrun — 24 hours is insufficient** to build pipeline + UI + fine-tune + evaluate + deploy. | High | Strict hour-by-hour schedule (see clarke_PRD_implementation.md). Prioritised must-have vs nice-to-have list (Section 12 below). Cut fine-tuning if behind schedule (use base MedGemma 27B with extensive prompt engineering). Cut Ward Round mode. Cut MedASR evaluation against Whisper. |
| 4 | **MedASR ambient performance degrades significantly** vs. single-speaker dictation. MedASR was trained on dictation, not two-party conversation. | Medium | Use high-quality pre-recorded demo audio (clear, studio conditions, 16kHz WAV). If WER >15% on ambient clips: use dictation-style audio for demo (clinician dictates post-consultation rather than ambient capture). Document ambient limitation as a production fine-tuning target. |
| 5 | **HAPI FHIR server setup is slow or fails** within HF Spaces Docker environment. | Medium | Pre-build and test the Docker configuration locally before deploying to HF Spaces. Fallback: replace live FHIR server with a mock FHIR API (FastAPI endpoints returning pre-loaded Synthea JSON). The demo UX is identical either way. |
| 6 | **Fine-tuning MedGemma 27B exceeds A100 40GB VRAM or takes >3 hours.** | Medium | QLoRA with 4-bit base reduces training VRAM to ~20GB. If still OOM: reduce LoRA rank from 16 to 8, reduce max_seq_length from 4096 to 2048, reduce training set from 250 to 100 examples. If training exceeds time budget: skip fine-tuning, use base model with engineered prompts, document fine-tuning plan in writeup. |
| 7 | **Synthetic training data quality is poor** (Claude-generated triplets are clinically implausible or badly formatted). | Medium | Manually review 20 of 250 training samples before committing to fine-tuning. If >20% fail quality check: regenerate with revised prompts, or reduce to a smaller but manually curated set. |

---

## 9. What Makes Clarke Superior?

### vs. Commercial Alternatives (Heidi Health, DAX Copilot, Nabla, Tortus, Accurx)

1. **Record context integration.** Every commercial ambient scribe generates documents from conversation alone. Clarke fuses conversation with actual EHR data — lab values, medication lists, allergy flags — producing documents no conversation-only scribe can match. This is a structural architectural advantage, not a feature that competitors can easily bolt on (their cloud architecture has no connection to the hospital's FHIR server).
2. **Privacy by design.** All processing is local. Zero patient data leaves the hospital. This directly addresses the NHS's most critical barrier to AI adoption (data sovereignty), which every cloud-dependent competitor fails.
3. **Zero marginal cost.** Open-source, open-weight. NHS trusts pay for GPU hardware once (~£5k–£15k) versus >£2M/year in licensing fees for Heidi at scale across a trust.
4. **Auditability.** Open code and open model weights satisfy NHS Information Governance requirements for AI transparency. Commercial scribes are black boxes.
5. **NHS-specific format.** Fine-tuned on NHS clinical letter conventions, not US SOAP notes.

### vs. Likely Competing Submissions

Based on the current Kaggle leaderboard (129 submissions from 5,855 entrants as of 12 Feb), the most visible submissions are medical chatbots, radiology triage tools, and single-model applications. Clarke's advantages:

1. **Three-model agentic pipeline.** Most submissions use one HAI-DEF model. Clarke uses three in a coordinated pipeline, directly addressing the "fullest potential" criterion.
2. **Clinician-validated problem.** Backed by a 47-respondent clinician survey and five peer-reviewed studies, not hypothetical.
3. **Real EHR integration (via FHIR).** Most submissions don't touch EHR data. Clarke's FHIR agent demonstrates a production-plausible integration path.
4. **Fine-tuned model with public adapter.** Releasing a LoRA adapter on HF Hub is a bonus submission element that few competitors will have.

### Unfair advantage

The project lead is an NHS clinician who has lived the problem, conducted the clinician survey, and can articulate the pain with first-hand specificity. This authenticity will be visible in the video and writeup — something no purely technical team can replicate.

---

## 10. How Does Clarke Align to the Judging Criteria?

| Criterion (Weight) | Clarke's Alignment | How We Score Maximally |
|---|---|---|
| **Effective use of HAI-DEF models (20%)** | Three HAI-DEF models, each chosen with quantified justification over general alternatives. Pipeline creates emergent value (conversation + record context → enriched document). LoRA fine-tuning adapts MedGemma 27B beyond its default task. MedGemma 1.5 4B's new EHR understanding capability is directly exploited. | Publish LoRA adapter on HF Hub. Include WER comparison (MedASR vs Whisper). Show pipeline synergy explicitly in video (side-by-side: transcript-only letter vs context-enriched letter). |
| **Problem Domain (15%)** | NHS workforce crisis backed by TACT study, GMC NTS 2025, BMA data, and a 47-respondent clinician survey. Clear target user (NHS doctors). Named competitors with specific shortcomings. | Open the video with a compelling human story (the 4:1 admin-to-patient ratio). Use one powerful survey quote. Keep the problem statement visceral, not abstract. |
| **Impact Potential (15%)** | £1.07B annual value. 11,888 FTE equivalent. 13-point burnout reduction. Each estimate sourced from peer-reviewed literature. Honest caveats included. | Present a single high-impact table in the writeup. State caveats upfront — honesty builds credibility with Google Research judges. |
| **Product Feasibility (20%)** | Working live demo on HF Spaces. Complete tech stack. Evaluation metrics (WER, BLEU, ROUGE-L, fact recall). Deployment challenges with specific mitigations. Production path described. | Ensure the demo works flawlessly for the video. Include one quantitative evaluation chart in writeup. Address GPU cost and NHS accent diversity in deployment section. |
| **Execution & Communication (30%)** | Polished video ≤3 min. Writeup ≤1,500 words following template. Public GitHub repo with clean code and README. Public HF Space. Public HF LoRA adapter. Cohesive narrative across all materials. | Video: high production value (screen recording with voiceover, not talking head). Writeup: every word earns its place. Code: module-level docstrings, inline comments, architecture diagram in README. Narrative: "3 models, 1 pipeline, 0 data leaves" as recurring motif. |

---

## 11. Quantifiable Success Criteria

The project is complete and competition-ready when ALL of the following are true:

| # | Criterion | Measurable Threshold |
|---|---|---|
| 1 | End-to-end pipeline runs | Select patient → record audio → stop → draft letter appears. No crashes. |
| 2 | Draft letter latency | <60 seconds from "End Consultation" click to rendered letter. |
| 3 | Draft letter quality | 5/5 demo scenario letters are clinically coherent, include FHIR-sourced values, and follow NHS letter structure (manual review). |
| 4 | MedASR evaluation | WER computed on ≥20 test clips. MedASR WER < Whisper WER on medical dictation. |
| 5 | EHR Agent evaluation | Fact recall >85%, precision >90%, hallucination rate <10% on 20 test patients. |
| 6 | Fine-tuned MedGemma 27B | LoRA adapter trained. BLEU/ROUGE-L computed on 50 test triplets. Fine-tuned scores > baseline. |
| 7 | Live public demo | HF Space URL is accessible from any browser (incognito test). |
| 8 | Public code repository | GitHub repo is public. Contains README with architecture diagram, setup instructions, evaluation results, licence. All .py files have docstrings. |
| 9 | Public LoRA adapter | HF Hub model repo is public, traces to `google/medgemma-27b-text-it`. |
| 10 | Video | ≤3 minutes. Demonstrates complete pipeline. Covers all 5 judging criteria. Visually polished. |
| 11 | Writeup | ≤1,500 words. Follows required template (Project name, Team, Problem statement, Overall solution, Technical details). All required links included. |
| 12 | Kaggle submission | Writeup submitted via Kaggle Writeups tab. Agentic Workflow Prize selected. |

---

## 12. Must-Haves vs. Nice-to-Haves

If time runs short, protect everything above the line. Cut everything below.

### Must-Haves (Non-Negotiable)

1. **Working MedASR transcription pipeline** — audio in, text out.
2. **Working MedGemma 4B EHR Agent** — patient ID in, structured context JSON out (even if from mock FHIR API).
3. **Working MedGemma 27B document generation** — transcript + context in, NHS letter out (even with base model, no fine-tuning).
4. **End-to-end orchestration** — all three stages connected and producing output from a single user action.
5. **Functional Gradio UI** — patient selection, recording controls, context panel, document display, basic editing.
6. **3 demo scenarios tested** — Mrs Thompson (diabetes), Mr Okafor (chest pain), Ms Patel (asthma). Pre-recorded audio.
7. **Public HF Space deployment** — live, accessible demo.
8. **Public GitHub repo** — clean code, README, licence.
9. **3-minute video** (can be recorded Mon 16 Feb).
10. **Writeup** (can be written Mon 16 Feb).

### Nice-to-Haves (Cut If Behind Schedule)

11. LoRA fine-tuning of MedGemma 27B (fall back to prompt engineering).
12. Public HF LoRA adapter repo.
13. Quantitative MedASR evaluation (WER comparison vs Whisper).
14. Quantitative EHR Agent evaluation (fact recall, precision).
15. BLEU/ROUGE-L evaluation of document generation.
16. Ward Round mode.
17. Discrepancy flagging (allergy mismatch alerts).
18. PDF export functionality.
19. FHIR DocumentReference export.
20. NHS Design System visual polish (accessibility scores, responsive breakpoints).

**Decision rule:** At the end of Day 2 (Hour 16), assess progress against the must-have list. If ≥2 must-haves are incomplete, cancel all nice-to-haves and focus exclusively on completing the core pipeline and deployment.

---

*This document is the north star for all Clarke PRDs. Every implementation decision, design choice, and task-level instruction in the derivative PRDs must be traceable to a goal, constraint, or success criterion defined here.*
