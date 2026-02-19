# Clarke — Product Specification Document

**Version:** 2.0  
**Date:** 12 February 2026  
**Purpose:** Comprehensive specification for PRD generation and AI-agent execution within 24 working hours  
**Competition:** MedGemma Impact Challenge (Kaggle)  
**Targets:** Main Track 1st Place ($30,000) + Agentic Workflow Prize ($5,000)

---

## SECTION 1: PRODUCT VISION

### 1.1 Clarke in One Sentence

Clarke is an open-source, privacy-preserving AI system that listens to a clinician's patient consultation, automatically retrieves the relevant patient record context, and generates a complete, structured clinical document — ready to review and sign off — using a pipeline of three purpose-built HAI-DEF medical models (MedASR → MedGemma 4B → MedGemma 27B) running entirely within the hospital network.

### 1.2 The 30-Second Pitch

You talk to your patient. Clarke listens. In the background, it simultaneously pulls the patient's history, medications, recent bloods, and imaging results from the electronic health record. By the time you say goodbye, a draft clinic letter — structured to NHS standards, populated with the right investigation results, and chronologically ordered — is waiting on your screen. You review it, make any edits, and sign off. No dictaphone. No secretary. No 15-minute write-up from memory. No logging into five separate systems. Your letter is done before your next patient walks in. And no patient data ever leaves the building.

### 1.3 The Core Synergy: Why Combining Ambient Documentation with EHR Navigation Creates a Product Greater Than the Sum of Its Parts

The two capabilities are not merely additive — they solve each other's critical weakness.

**Ambient documentation alone** (CliniScribe) captures what was *said* in the consultation but is blind to what already *exists* in the patient record. A clinician discusses a rising HbA1c, but the scribe has no access to the actual lab values, the trend over the past 6 months, or the current medication list. The clinician must still manually look up and insert this information, or the generated letter is incomplete. This is exactly why commercial ambient scribes like Heidi Health and DAX Copilot still require significant post-generation editing — they produce notes from conversation alone, without record context.

**EHR navigation alone** (WardBrief) retrieves and summarises existing patient data but cannot capture what happens *during* the consultation — the new symptoms reported, the examination findings, the shared decision-making, the agreed plan. It produces a pre-consultation briefing, not a post-consultation document.

**Clarke unifies both pipelines through a single integration point:** the conversation transcript (produced by MedASR) is passed to MedGemma 27B *alongside* the structured patient context (retrieved by MedGemma 4B acting as a FHIR agent). This means the document-generation model has access to both what the clinician discussed *and* what the record contains. The result is a clinical letter that:

- References actual lab values discussed ("Your HbA1c has risen from 48 to 55 mmol/mol since June 2025") rather than vague mentions ("blood sugar levels were discussed")
- Includes the current medication list without the clinician having to dictate it
- Automatically attaches relevant investigation results referenced during the conversation
- Cross-checks for consistency — if the clinician mentions "no allergies" but the record shows a penicillin allergy, Clarke flags the discrepancy

This integration transforms Clarke from a transcription tool into a **clinical reasoning assistant** that produces documents no standalone ambient scribe or EHR navigator could match.

**For the Agentic Workflow Prize specifically:** this pipeline — audio capture → medical speech recognition → agentic EHR data retrieval → context-enriched document generation → clinician review — constitutes a five-stage agentic workflow where three HAI-DEF models operate as intelligent agents, each making autonomous decisions about what to process and retrieve. This is precisely the "significant overhaul of a challenging process" the prize description calls for.

---

## SECTION 2: THE PROBLEM

### 2.1 Problem Definition

NHS doctors spend four hours on administrative tasks for every one hour with patients, with clinical documentation — writing letters, discharge summaries, referral notes, and ward round entries — consuming the largest share of that administrative time. This documentation requires clinicians to assimilate information scattered across multiple disconnected IT systems, compose structured clinical narratives, and ensure accuracy, all under severe time pressure. The result is a workforce crisis: doctors burning out, leaving the profession, and — critically — spending less time with the 7.3 million patients currently waiting for NHS treatment.

### 2.2 Quantified Magnitude

**(a) Affected clinicians.** The NHS employs 151,980 FTE hospital and community health service doctors and 38,220 FTE GPs in England alone — approximately 190,200 FTE doctors total [NHS Digital Workforce Statistics, August 2025; General Practice Workforce, December 2025]. Adding Scotland, Wales, and Northern Ireland brings the UK total to approximately 210,000 practising doctors. All of them document clinical encounters.

**(b) Time lost per clinician per day.** The TACT study (Time Allocation in Clinical Training), a national multicentre observational study of 137 NHS resident doctors observed across secondary care centres over 7 months (January–July 2024), found that doctors spent only 17.9% of their time on patient-facing activities while 73.0% was consumed by non-patient-facing tasks [Arab et al., QJM: An International Journal of Medicine, June 2025, doi:10.1093/qjmed/hcaf141]. Our own clinician survey (n=47, January–February 2026) confirmed that documentation specifically accounts for approximately 15 minutes per patient encounter, with clinicians seeing 10–12 patients per half-day clinic — yielding 2.5–3 hours of documentation time per clinic session.

**(c) National aggregate impact.**

- **Time:** If 190,200 FTE NHS doctors in England each save 30 minutes per day (the figure demonstrated by Olson et al., JAMA Network Open 2025), that yields **95,100 clinician-hours freed per day** — equivalent to approximately **11,888 additional full-time doctors** (at 8 hours/day). The NHS currently has 7,248 medical vacancies in secondary care alone [NHS Digital, September 2025]. Clarke's time savings could effectively fill more vacancies than currently exist.
- **Money:** The mean annual basic pay per FTE doctor is £90,290 [NHS Digital, August 2025]. The 30-minute daily saving per doctor equates to £5,642 per doctor per year in reclaimed clinical time, or **£1.07 billion annually** across 190,200 NHS doctors in England.
- **Career:** The GMC's 2025 National Training Survey found 61% of trainees at moderate or high risk of burnout [GMC NTS 2025; NHS Employers]. The 2024 NHS Staff Survey reported 42.19% of medical and dental staff experience work-related stress and 30.24% feel burnt out [BMA, Medical Staffing Data Analysis]. The JAMA Network Open study demonstrated that ambient AI scribes reduced burnout from 51.9% to 38.8% (OR 0.26, 95% CI 0.13–0.54, p<0.001) after just 30 days [Olson et al., JAMA Netw Open 2025;8(10):e2534976].
- **Waiting list:** 7.31 million cases on the NHS waiting list as of November 2025, with only 62% of patients treated within 18 weeks against a 92% constitutional standard [BMA Backlog Data Analysis; King's Fund]. Every hour freed from documentation is an hour available for patient care.

**(d) Patient safety consequences.** The TACT study found that junior trainees (FY1–ST5) spent only 17.8% of time on patient-facing tasks versus 38.4% for senior trainees (ST6–8) — meaning the least experienced doctors have the least patient contact and the most administrative burden [Arab et al., 2025]. The GMC 2025 NTS found 21% of trainees hesitated to escalate patient care concerns [GMC NTS 2025]. Fragmented records directly contribute to safety incidents: our survey respondents described emergency situations where patients were "unconscious, confused, or unable to speak" and "missing one piece of information like an allergy or heart condition could cause serious harm."

### 2.3 Unmet Need — Why Existing Solutions Fall Short

| Competitor | What It Does | Why It Falls Short for NHS Clinicians |
|---|---|---|
| **Microsoft DAX Copilot (Nuance)** | Cloud-based ambient scribe integrated with Epic/Oracle | Sends patient audio to US-hosted cloud servers — violates NHS data sovereignty requirements. Requires enterprise EHR integration (Epic). Costs >$200/clinician/month at scale. Generates American-style documentation, not NHS clinical letters. |
| **Heidi Health** | Cloud-based ambient scribe with NHS GP traction (claims 60% of NHS GPs) | Closed-source, proprietary — NHS trusts cannot audit the model. Cloud-dependent ($99/month per clinician). No EHR record integration — generates notes from conversation only, without access to patient history, lab results, or imaging. Produces documentation that still requires manual enrichment with record data. |
| **Abridge** | Ambient AI scribe deployed at Yale, UCSF, and other US health systems | US-focused, no NHS deployment. Cloud-only architecture. No FHIR-based record navigation. |
| **Nabla** | European ambient scribe | Cloud-dependent. Limited NHS integration. No record context retrieval. |
| **Tortus AI / Accurx Scribe** | UK-based ambient scribes with NHS deployments | Accurx claims 97% clinical accuracy but is a closed proprietary solution with no EHR data retrieval. Tortus operates across 3,500+ GP practices but is cloud-dependent and subscription-based. Neither provides intelligent record navigation. |
| **Existing EHR systems (Cerner, EMIS, SystmOne)** | Store and display patient records | Present data in silos across separate modules. No synthesis, no summarisation, no document generation from conversation. Clinicians must manually navigate and compile information. |

**The specific unmet need Clarke addresses:** An open-source, fully local, NHS-tailored AI system that combines ambient clinical documentation with intelligent EHR record retrieval — producing context-enriched clinical documents from conversation, without patient data leaving the hospital, at zero per-clinician licensing cost.

No existing product does both. Every commercial ambient scribe generates documents from conversation alone, without EHR context. Every EHR system presents records without document generation. Clarke is the first system to close this loop using purpose-built medical AI models that can be audited, customised, and deployed entirely on-premise.

---

## SECTION 3: HOW CLARKE WORKS — END-TO-END

### 3.1 Complete User Journey

**Pre-consultation (30 seconds):**

1. The clinician opens Clarke in their web browser (accessible on any device connected to the hospital network). They see a clean dashboard showing their clinic list for the day — patient names, appointment times, and brief one-line summaries.
2. They click on the next patient's name. Clarke's EHR Agent (MedGemma 4B) begins retrieving patient context in the background via FHIR API calls: demographics, problem list, current medications, recent blood results, recent imaging reports, and the last clinic letter.
3. A "Patient Context" panel populates on the left side of the screen, showing a structured summary: key diagnoses, current medications, recent investigations with trends, and any flags (e.g., allergies, pending results). This takes 5–10 seconds.

**During consultation (10–30 minutes):**

4. The clinician clicks "Start Consultation." Clarke activates the microphone. A small recording indicator appears at the top of the screen.
5. The clinician has their normal conversation with the patient. They can glance at the Patient Context panel at any time for reference.
6. MedASR processes the audio stream in real-time, producing a running transcript visible in a "Live Transcript" tab (minimised by default, expandable if the clinician wants to check).
7. If the clinician mentions specific results ("Your kidney function has gotten a bit worse"), Clarke's EHR Agent can dynamically fetch the relevant lab values and queue them for inclusion in the document.

**Post-consultation (15–60 seconds):**

8. The clinician clicks "End Consultation." The recording stops.
9. Clarke sends the complete transcript (from MedASR) and the patient context (from the EHR Agent) to MedGemma 27B, which generates a structured clinical document.
10. Within 10–30 seconds, a draft document appears in the main panel. It is structured as an NHS clinic letter with: date, patient demographics, addressee (GP), reason for consultation, history of presenting complaint, relevant past medical history, examination findings, investigation results (with actual values from the EHR), assessment, and plan.
11. The clinician reviews the document. They can:
    - Edit any text directly (inline editing)
    - Click on any cited investigation result to see the source record
    - Accept or reject individual sections
    - Use a "Regenerate" button on any section to get an alternative phrasing
12. Once satisfied, they click "Sign Off." The document is marked as approved and ready for export.
13. The document can be exported as: a PDF, a FHIR DocumentReference resource for EHR integration, or copied to clipboard for pasting into the existing EHR system.
14. Clarke resets. The clinician clicks the next patient. The cycle begins again.

**Ward Round Mode (alternative flow):**

For inpatient settings, Clarke offers a "Ward Round" mode. Instead of recording a single extended consultation, it records the ward round conversation for each patient sequentially. The clinician taps "Next Patient" as they move between beds. For each patient, Clarke generates a ward round entry (not a letter) containing: overnight events, current status, examination findings, investigation results, and today's plan. This mode produces a daily progress note rather than a clinic letter, but uses the same underlying pipeline.

### 3.2 System Architecture — Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLARKE SYSTEM                            │
│                                                                 │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────────────┐ │
│  │ Browser  │◄──►│ Gradio 5.x│◄──►│     Orchestrator          │ │
│  │ (User)   │    │ Frontend  │    │   (Python / FastAPI)       │ │
│  └──────────┘    └───────────┘    └────────┬─────────┬────────┘ │
│                                            │         │          │
│                    ┌───────────────────┐    │         │          │
│                    │                   │    │         │          │
│              ┌─────▼─────┐     ┌──────▼────▼──┐     │          │
│              │  MedASR    │     │  MedGemma     │     │          │
│              │  (105M)    │     │  1.5 4B       │     │          │
│              │            │     │  EHR Agent    │     │          │
│              │ Audio→Text │     │  FHIR→Context │     │          │
│              └─────┬──────┘     └──────┬────────┘     │          │
│                    │                   │              │          │
│                    │    TRANSCRIPT     │   PATIENT    │          │
│                    │                   │   CONTEXT    │          │
│                    │                   │              │          │
│                    └────────┬──────────┘              │          │
│                             │                        │          │
│                    ┌────────▼────────┐               │          │
│                    │   MedGemma 27B  │               │          │
│                    │   (text-only)   │               │          │
│                    │                 │               │          │
│                    │ Transcript +    │               │          │
│                    │ Context →       │               │          │
│                    │ Clinical Letter │               │          │
│                    └────────┬────────┘               │          │
│                             │                        │          │
│                    ┌────────▼────────┐               │          │
│                    │  Draft Document │               │          │
│                    │  (Structured)   │◄──────────────┘          │
│                    └─────────────────┘                           │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ FHIR Server  │ (Synthea synthetic data for demo;             │
│  │ (HAPI FHIR)  │  real hospital FHIR server in production)     │
│  └──────────────┘                                               │
│                                                                 │
│            ALL PROCESSING WITHIN HOSPITAL NETWORK               │
└─────────────────────────────────────────────────────────────────┘
```

**Detailed Data Flow:**

**Stage 1 — Audio Capture → Medical Transcript**
- **Model:** MedASR (`google/medasr` on Hugging Face). 105M parameters. Conformer-based ASR.
- **Input:** Mono-channel audio stream, 16kHz, int16 waveform. Captured via browser MediaRecorder API, chunked and sent to backend via WebSocket.
- **Processing:** Audio chunks processed using `transformers` pipeline with `chunk_length_s=20` and `stride_length_s=2` for streaming transcription.
- **Output:** Full-text transcript of the clinician-patient conversation.

**Stage 2 — Agentic EHR Context Retrieval**
- **Model:** MedGemma 1.5 4B multimodal, instruction-tuned (`google/medgemma-1.5-4b-it` on Hugging Face). 4B parameters.
- **Architecture:** Operates as a LangGraph-based agent following Google's EHR Navigator pattern. The agent receives a clinical query (e.g., "Retrieve patient context for consultation"), discovers available FHIR resources, plans which to retrieve, fetches them via FHIR REST API calls, extracts relevant facts, and synthesises a structured context summary.
- **Input:** Patient identifier + clinical query (initially "Prepare pre-consultation summary"; updated dynamically during consultation if specific results are mentioned in the transcript).
- **FHIR Resources Queried:** Patient, Condition, MedicationRequest, Observation (labs), DiagnosticReport, AllergyIntolerance, Encounter (recent), DocumentReference (last clinic letter).
- **Output:** Structured JSON containing: demographics, problem list, current medications, allergies, recent lab results (with values, units, reference ranges, and dates), recent imaging summaries, and key excerpts from the most recent clinic letter.

**Stage 3 — Context-Enriched Document Generation**
- **Model:** MedGemma 27B text-only, instruction-tuned (`google/medgemma-27b-text-it` on Hugging Face). 27B parameters.
- **Input:** A structured prompt containing:
  1. The full conversation transcript (from Stage 1)
  2. The structured patient context JSON (from Stage 2)
  3. A document template specifying the target format (NHS clinic letter, discharge summary, ward round note, or referral letter — selected by the clinician)
  4. Instructions for clinical document conventions (chronological ordering, inclusion of positive and negative findings, reference to specific investigation values)
- **Output:** A structured clinical document in the specified NHS format, with inline references to the source data (e.g., lab values traced to specific FHIR Observation resources).

**Integration Point:** The orchestrator (Python/FastAPI) coordinates all three stages. The transcript and patient context are combined into a single prompt for MedGemma 27B. This is the critical fusion that no existing product achieves — the document generator sees both the conversation and the record simultaneously.

### 3.3 HAI-DEF Model Justification

**MedASR (105M, `google/medasr`):**

(a) *Why not a general-purpose ASR like Whisper?* MedASR achieves 5.2% WER on chest X-ray dictation compared to 12.5% for Whisper large-v3 — 58% fewer transcription errors. On broad medical dictation, MedASR reaches 5.2% WER versus 28.2% for Whisper — 82% fewer errors [Google Research Blog, January 2026]. Medical terminology errors in transcription directly corrupt downstream document generation.

(b) *Exploited capability:* MedASR was specifically trained on ~5,000 hours of de-identified physician dictations across radiology, internal medicine, and family medicine [Google/MedASR Hugging Face Model Card]. It has a strong vocabulary for drug names, anatomical terms, and clinical phrases that general ASR models consistently misrecognise.

(c) *Beyond default use case:* MedASR was designed for single-speaker medical dictation. Clarke uses it for two-party ambient conversation (clinician + patient), which is significantly harder due to speaker overlap, non-medical language, and background noise. We fine-tune MedASR with LoRA on synthetic multi-speaker clinical conversations to improve ambient performance. [**Assumption:** ambient performance will degrade relative to single-speaker dictation; fine-tuning mitigates but may not fully close the gap.]

**MedGemma 1.5 4B Multimodal (`google/medgemma-1.5-4b-it`):**

(a) *Why not a general-purpose LLM for EHR navigation?* MedGemma 1.5 4B was specifically trained on FHIR-based EHR data and medical documents. Google's own EHR Navigator Agent notebook demonstrates this capability. A general-purpose model would need extensive prompting to understand FHIR resource structures; MedGemma 4B understands them natively. Furthermore, its 4B parameter count enables it to run on modest GPU hardware, making the agentic loop fast enough for real-time context retrieval (critical for the pre-consultation loading step).

(b) *Exploited capability:* FHIR-native EHR understanding, medical document comprehension, and structured data extraction from lab reports — all capabilities added in the 1.5 release [Google Research Blog, January 2026].

(c) *Beyond default use case:* Google's EHR Navigator demonstrates single-query Q&A over FHIR records. Clarke extends this to multi-step agentic retrieval with dynamic re-querying based on the live conversation transcript — if a clinician mentions a result that wasn't in the initial context fetch, the agent retrieves it on-the-fly.

**MedGemma 27B Text-Only (`google/medgemma-27b-text-it`):**

(a) *Why not a general-purpose LLM for document generation?* MedGemma 27B was trained on medical text, medical Q&A pairs, and EHR data. It is optimised for inference-time computation on medical reasoning tasks [MedGemma Technical Report, arXiv:2507.05201]. A general-purpose model of equivalent size would produce plausible-sounding but medically imprecise documents. MedGemma 27B's medical training means it understands which findings are clinically significant, how to order information in a clinical narrative, and when to include negative findings — all essential for a high-quality clinical letter.

(b) *Exploited capability:* Medical text generation with clinical reasoning. The model can infer that if a patient is on metformin and their HbA1c has risen, this is clinically significant and should be prominently documented.

(c) *Beyond default use case:* MedGemma 27B is designed for medical question-answering and reasoning. Clarke uses it for structured document generation to NHS clinical letter standards, which requires not just medical knowledge but understanding of UK healthcare documentation conventions. We fine-tune it on exemplar NHS clinical letters using LoRA to instil these conventions.

---

## SECTION 4: WHAT MAKES CLARKE SUPERIOR

### 4.1 Why HAI-DEF Models Are Superior to General-Purpose Alternatives

**(a) Versus GPT-4 / Gemini:** Three concrete advantages:

1. **Privacy.** GPT-4 and Gemini require cloud API calls, sending patient audio and clinical data to third-party servers. Our clinician survey recorded a respondent stating: "Complete and unbreakable privacy would be non-negotiable. Any data sent to US companies (even if their servers are in the UK) would not be private." HAI-DEF models are open-weight and run locally. Zero patient data leaves the hospital.
2. **Medical accuracy.** MedASR outperforms Whisper (a general-purpose ASR comparable to what GPT-4's speech mode uses) by 58–82% on medical dictation WER [Google Research Blog, January 2026]. MedGemma 4B's FHIR understanding is native, not prompt-engineered.
3. **Cost at scale.** A one-time GPU infrastructure investment versus perpetual per-clinician API fees. At 190,200 NHS doctors, even $0.10 per consultation at 20 consultations/day = $380,400/day in API costs. Local HAI-DEF deployment: $0 marginal cost per consultation.

**(b) Versus using each HAI-DEF model in isolation:** The pipeline creates emergent value. MedASR alone produces a transcript. MedGemma 4B alone produces a patient summary. MedGemma 27B alone could generate text from a prompt. But without the pipeline, the transcript has no record context, the summary has no consultation content, and the document generator has neither. The pipeline produces a document that is qualitatively different from what any individual model could generate — it is simultaneously grounded in the conversation and in the patient's medical record.

### 4.2 Why Clarke Could Be Superior to Heidi Health and Other Commercial Ambient Scribes

Heidi Health is the strongest current competitor in the NHS (claims 60% GP adoption, $65M Series B, 340,000 consultations/week) [TechFundingNews, October 2025]. Clarke's advantages are structural, not merely ideological:

1. **Record context integration.** Heidi generates notes from conversation only. Clarke generates documents enriched with actual EHR data — lab values, medication lists, allergy checks. This is not a feature Heidi can easily add because their architecture sends audio to their cloud for processing and has no connection to the hospital's FHIR server. Clarke's local deployment enables direct FHIR server access.

2. **Clinical safety through cross-referencing.** Because Clarke sees both the conversation and the record, it can flag discrepancies (e.g., clinician says "no known allergies" but record shows penicillin allergy). No conversation-only scribe can do this.

3. **Zero marginal cost.** Heidi charges $99/month per clinician. For 190,200 NHS doctors, that is $226 million/year. Clarke is open-source with zero licensing cost. The only cost is GPU hardware, which NHS trusts already possess or can acquire as a one-time capital expenditure.

4. **Auditability.** NHS Information Governance requires that AI systems processing patient data be auditable. Heidi is a closed-source black box. Clarke's code and model weights are fully inspectable.

5. **NHS document format compliance.** Clarke is fine-tuned specifically on NHS clinical letter templates. Heidi generates generic notes that clinicians must reformat.

### 4.3 Special Technology Prize: Agentic Workflow Prize

Clarke targets the **Agentic Workflow Prize** ("the project that most effectively reimagines a complex workflow by deploying HAI-DEF models as intelligent agents or callable tools").

The combined product gives a stronger case than either idea alone because it demonstrates a **multi-model agentic pipeline** where:

- MedASR operates as an autonomous audio processing agent
- MedGemma 4B operates as an autonomous EHR navigation agent (planning FHIR queries, deciding which resources to retrieve, extracting relevant facts)
- MedGemma 27B operates as an autonomous document generation agent (deciding structure, selecting relevant information, generating prose)
- The orchestrator coordinates these three agents into a cohesive workflow

A documentation-only tool (CliniScribe) would demonstrate a two-stage pipeline. A navigation-only tool (WardBrief) would demonstrate a single-agent system. Clarke demonstrates a **three-model, five-stage agentic workflow** that fundamentally reimagines the entire clinical documentation process from audio capture to signed-off letter.

---


## SECTION 5: IMPACT QUANTIFICATION

### 5.1 Impact Estimation Table

| # | Metric | Estimate | Calculation Method | Source |
|---|---|---|---|---|
| 1 | **Documentation time saved per clinician per day** | 30 minutes | Direct measurement: 263 physicians across 6 US health systems, pre-post ambient AI scribe deployment over 90 days. Measured via EHR time-stamp logs. | Olson et al., JAMA Netw Open 2025;8(10):e2534976 |
| 2 | **Documentation time saved per patient encounter** | ~15 minutes | Clinician self-report from 47 NHS clinicians. Direct quote: "save me 15 mins for every patient." Consistent with 30 min/day ÷ 2 encounters/hour. | MedGamma Clinician Survey, Jan–Feb 2026 (n=47) |
| 3 | **After-hours documentation ("pajama time") reduction** | 42% decrease in after-hours EHR work; 66% decline in documentation delays | Retrospective study of 181 primary care physicians and APPs across 14 practices using hybrid ambient AI + virtual scribe. | Moura et al., J Gen Intern Med 2025. DOI:10.1007/s11606-025-09979-5 |
| 4 | **Total EHR time reduction per note** | 15% less total EHR time; >15% less note-composing time specifically | Matched cohort comparison of 704 primary care clinicians (239 ambient AI users vs. 465 controls) at UChicago Medicine over 90 days. | Pearlman et al., JAMA Netw Open 2025;8(10):e2537000 |
| 5 | **NHS doctors who benefit (England)** | 190,200 FTE | 151,980 FTE HCHS doctors + 38,220 FTE GPs. | NHS Digital Workforce Statistics Aug 2025 + GP Workforce Dec 2025 |
| 6 | **Clinician-hours freed daily (England)** | 95,100 hours/day | 190,200 doctors × 0.5 hours saved/day. | Calculated from rows 1 + 5 |
| 7 | **Equivalent full-time doctors freed** | ~11,888 FTE | 95,100 hours ÷ 8 hours/day. For context: NHS had 7,248 medical vacancies in secondary care alone (Sep 2025). | Calculated; vacancy figure from NHS Digital |
| 8 | **Annual financial value of reclaimed time** | £1.07 billion | 190,200 × (30 min/day × 250 working days/year) × (£90,290 mean annual salary ÷ 2,000 working hours/year) = 190,200 × £5,642 = £1.07B. | NHS Digital mean doctor salary Aug 2025 + calculation |
| 9 | **Burnout prevalence reduction (documentation-specific)** | 21.2 percentage-point absolute reduction at 84 days | Pre-post survey of 873 physicians and APPs piloting ambient AI at Mass General Brigham. Survey response rates: 30% at 42 days, 22% at 84 days. | You et al., JAMA Netw Open 2025. DOI:10.1001/jamanetworkopen.2025.28056 |
| 10 | **Overall burnout reduction (comprehensive measure)** | 13.1 percentage points (51.9% → 38.8%; OR 0.26, 95% CI 0.13–0.54, p<0.001) at 30 days | Pre-post measurement across 263 physicians at 6 health systems. | Olson et al., JAMA Netw Open 2025;8(10):e2534976 |
| 11 | **Documentation well-being improvement** | 30.7 percentage-point absolute increase at 60 days | Pre-post survey of 557 clinicians (attending physicians, APPs, residents, fellows) at Emory Healthcare. 11% response rate. | You et al., JAMA Netw Open 2025 (Emory arm) |
| 12 | **Ward round preparation time saved (EHR navigation)** | 25–50 minutes per ward round | Currently 30–60 min to prepare a 10–12 patient ward round (multi-system login, data compilation). Reduced to 5–10 min with automated FHIR context retrieval. | Clinician survey descriptions + clinical workflow estimate |
| 13 | **Patient safety: missing clinical information** | 15% of outpatient consultations have missing key information; of those, 32% experience care delays, 20% have documented risk of harm | Prospective study across 3 UK teaching hospitals. Extrapolation: ~10M outpatients/year seen without key info nationally, ~2M at risk of harm. | Burnett et al., BMC Health Serv Res 2011;11:114 |
| 14 | **Patient safety: clinical negligence cost** | £4.6 billion annual cost of harm (2024/25); £60.3 billion total provision for future liabilities | NHS Resolution annual report. 14,428 new clinical negligence claims received in 2024/25. Documentation failures are a contributory factor in many claims. | NHS Resolution Annual Report 2024/25 |
| 15 | **Commercial licensing cost avoided** | £226 million/year | 190,200 doctors × $99/month (Heidi Health pricing) × 12 months × 0.79 GBP/USD. Clarke's open-source model: £0 licensing. Hardware cost: £5K–£15K per trust (one-time). | Heidi Health pricing + calculation |

### 5.2 Honest Caveats

**1. The 30-minute daily saving comes from US ambulatory care, not NHS settings.** The Olson et al. and Pearlman et al. studies measured US clinicians generating SOAP notes in 15–20 minute primary care visits. NHS workflows differ structurally: GP consultations are typically 10 minutes, hospital clinics vary by specialty, and the documentation output is an NHS-format clinical letter (not a SOAP note). The actual NHS saving could be higher (because NHS clinicians still use dictaphones and manual secretary workflows, which are slower than the US EHR-based systems that ambient AI was compared against) or lower (because shorter consultations produce less source material for the AI). **Validation required:** A prospective time-motion study within a UK NHS pilot comparing Clarke to current documentation methods.

**2. MedASR has not been validated on NHS-accented English at scale.** The NHS workforce includes doctors from over 100 countries. MedASR was trained on ~5,000 hours of US-accented medical dictation. While its Conformer architecture handles accent variation better than RNN-based models, and its fine-tuning notebook enables LoRA adaptation to new accents, we have not empirically tested WER on South Asian, Nigerian, Middle Eastern, or Scottish-accented English — the dominant NHS demographic groups. **Assumption:** LoRA fine-tuning on 100–500 hours of NHS-accented audio will bring WER to within 2 percentage points of the US baseline. This assumption has not been validated.

**3. FHIR API availability varies across NHS trusts.** NHS England's Interoperability Standards mandate FHIR exposure, but adoption is uneven. Some trusts (especially those on EMIS or SystmOne) have robust FHIR endpoints; others (especially legacy Cerner/Oracle Health sites) have limited FHIR R4 support. Clarke degrades gracefully — it operates in "documentation-only" mode without FHIR — but the full value proposition requires FHIR access. **Validation required:** Survey of FHIR readiness across target pilot trusts before deployment.

**4. Burnout reduction figures may not transfer to UK clinicians.** The You et al. study (Mass General Brigham/Emory) involved self-selected pilot users with modest response rates (22–30% at MGB; 11% at Emory), likely overrepresenting enthusiastic adopters. The Olson et al. study had stronger methodology but was still US-based. NHS burnout drivers include non-documentation factors (understaffing, pay disputes, waiting list pressure) that ambient AI cannot address. **Assumption:** Clarke will reduce documentation-related burnout but will not solve systemic NHS workforce issues.

**5. AI-generated clinical documents will contain errors.** MedGemma 27B may hallucinate clinical findings, misattribute lab values, or generate imprecise medical terminology. The FHIR agent may fail to retrieve relevant records or retrieve irrelevant ones. MedASR will produce transcription errors, especially in noisy clinical environments. Clinician review and sign-off is mandatory for every document — Clarke is an authoring aid, not an autonomous documentation system. Google explicitly states HAI-DEF model outputs require independent professional verification.

**6. The financial impact estimate (£1.07B) assumes the reclaimed time is used productively.** In reality, some freed time will be absorbed by other administrative tasks, meetings, or systemic inefficiencies. The per-doctor financial value is calculated at the average salary rate; the true value depends on whether freed time translates to additional patient encounters or clinical activity.

---

## SECTION 6: TECHNICAL FEASIBILITY & 3-DAY BUILD PLAN

### 6.1 Hour-by-Hour Build Plan (24 Working Hours)

**DAY 1 — FRIDAY 13 FEBRUARY (Hours 1–8): Foundation + Core Model Pipelines**

| Hour | Task | Tools / Libraries | Deliverable | "Done" Criterion |
|---|---|---|---|---|
| 1 | **Environment setup.** Provision Hugging Face Space with A100 40GB GPU. Install Python 3.11, PyTorch 2.4.x, transformers, FastAPI, Gradio. Clone starter repo. | HF Spaces (Docker `nvidia/cuda:12.4.1-runtime-ubuntu22.04`), `pip`, `git` | Running HF Space with GPU confirmed via `torch.cuda.is_available()` | Space boots, GPU confirmed, all core packages import without error |
| 2 | **Synthetic FHIR data generation.** Generate 50 UK-style synthetic patients using Synthea. Load into HAPI FHIR server (Docker container within Space). Configure patient names, NHS numbers, UK drug formulary, mmol/L units. | Synthea v3.3.0 (Java CLI), HAPI FHIR v7.4 (Docker), `requests` for REST verification | 50 patient records accessible via `GET /fhir/Patient` | `curl http://localhost:8080/fhir/Patient?_count=50` returns 50 patients with UK-formatted data |
| 3 | **MedASR integration (Part 1).** Load `google/medasr` via `transformers` AutoModelForSpeechSeq2Seq pipeline. Build audio ingestion: browser MediaRecorder API → WebSocket → server-side WAV conversion (16kHz, mono, int16). | `transformers` 4.47.x, `librosa` 0.10.x, `pydub` 0.25.x, `ffmpeg` 7.x, `websockets` 12.x | Audio capture → WAV file on server | Record 30-second audio clip in browser → receive valid 16kHz WAV on server |
| 4 | **MedASR integration (Part 2).** Implement chunked transcription: `chunk_length_s=20`, `stride_length_s=2`, `return_timestamps=True`. Build real-time transcript WebSocket return to frontend. Test with sample medical dictation audio. | `transformers` pipeline, `torch`, custom WebSocket handler | Working audio → text pipeline with streaming output | Transcribe 5-minute medical dictation WAV with visible real-time text in browser console; visual inspection confirms <10% WER |
| 5 | **MedGemma 4B EHR Agent (Part 1).** Load `google/medgemma-1.5-4b-it` in 4-bit quantised mode. Implement LangGraph ReAct agent following Google's EHR Navigator pattern. Define FHIR tools: `search_patients`, `get_conditions`, `get_medications`, `get_observations`, `get_allergies`, `get_diagnostic_reports`. | `transformers`, `bitsandbytes` 0.44.x, `langgraph` 0.2.x, `httpx` for FHIR REST calls | Agent loads, tools callable, returns raw FHIR resources | Agent called with patient ID → returns raw Condition, MedicationRequest, Observation resources as JSON |
| 6 | **MedGemma 4B EHR Agent (Part 2).** Add context synthesis: agent extracts and structures facts from raw FHIR resources into a standardised JSON schema (demographics, problem_list, medications, allergies, recent_labs, recent_imaging, last_letter_excerpt). Add flags (rising trends, critical values, allergy alerts). | Custom JSON schema, `langgraph` state management | Structured patient context JSON for any synthetic patient | Agent returns well-formed JSON for 5 test patients; manual inspection confirms accuracy against FHIR data |
| 7 | **Orchestrator: connect MedASR + EHR Agent.** Build FastAPI orchestrator with endpoints: `POST /start-consultation` (activates audio capture + triggers EHR agent), `POST /end-consultation` (stops audio, sends transcript + context to document generation placeholder), `GET /patient-context/{id}` (returns pre-fetched context). | `FastAPI` 0.109.x, `uvicorn` 0.27.x, Python `asyncio` | Working orchestrator connecting both pipelines | Call `/start-consultation` with patient ID → EHR context loads while audio captures → call `/end-consultation` → receive combined prompt containing transcript + context |
| 8 | **Integration test + prompt engineering.** Design the document-generation prompt template: system message (NHS letter conventions), user message (transcript + context JSON + document type). Test with a mock transcript and real FHIR context, passing to MedGemma 27B placeholder (print output). Build 3 prompt variants: clinic letter, discharge summary, ward round note. | Custom Jinja2 templates, `jinja2` 3.1.x | 3 tested prompt templates producing correctly formatted combined prompts | Visual inspection of 3 generated prompts confirms correct structure: system instructions → transcript → FHIR context → format specification |

**DAY 2 — SATURDAY 14 FEBRUARY (Hours 9–16): Document Generation + UI + Fine-tuning**

| Hour | Task | Tools / Libraries | Deliverable | "Done" Criterion |
|---|---|---|---|---|
| 9 | **MedGemma 27B loading + baseline generation.** Load `google/medgemma-27b-text-it` in 4-bit quantisation via bitsandbytes (NF4, double quantisation, `compute_dtype=bfloat16`). Generate 5 baseline clinic letters from the 3 prompt templates using 5 synthetic patients. | `transformers`, `bitsandbytes` 0.44.x, `accelerate` 1.2.x | MedGemma 27B loaded, generates text | 5 generated letters saved as baseline for comparison. Model generates coherent medical text (even if format is not yet NHS-standard) |
| 10 | **Synthetic training data generation.** Generate 250 training triplets (transcript, FHIR context JSON, reference NHS clinic letter) using Claude API as a data generator. Each triplet based on a unique Synthea patient scenario. Apply NHS letter template conventions. Manually review 20 for quality. | `anthropic` SDK, Synthea data, custom generation scripts | 250 validated training triplets + 50 held-out test triplets in JSONL format | Training file (`train.jsonl`) and test file (`test.jsonl`) pass schema validation; 20 manually reviewed samples are clinically plausible and correctly formatted |
| 11 | **LoRA fine-tuning MedGemma 27B.** Fine-tune using QLoRA: base model 4-bit NF4, LoRA adapters on `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`. Hyperparameters: rank=16, alpha=32, dropout=0.05, learning_rate=2e-4, warmup_ratio=0.03, lr_scheduler=cosine, max_seq_length=4096, per_device_batch_size=2, gradient_accumulation_steps=8, epochs=3, optimizer=paged_adamw_8bit. | `peft` 0.13.x, `trl` 0.12.x (SFTTrainer), `bitsandbytes`, `datasets`, `wandb` for logging | Fine-tuned LoRA adapter saved to disk + training loss curve | Training completes without OOM. Final training loss < initial loss. Adapter file size < 500MB. |
| 12 | **Post-training evaluation.** Generate 50 test letters using fine-tuned model. Compute BLEU and ROUGE-L against held-out reference letters. Compare to 5 baseline letters from hour 9. Manual review of 10 generated letters for: (a) NHS format compliance, (b) clinical accuracy, (c) correct use of FHIR-sourced values, (d) appropriate positive and negative findings. | `evaluate` (HuggingFace), `rouge_score`, `sacrebleu`, manual review | Evaluation report: BLEU, ROUGE-L, qualitative assessment | Fine-tuned BLEU > baseline BLEU. Manual review confirms improved NHS format compliance. Report saved as `evaluation_report.md` |
| 13 | **Gradio UI (Part 1): core layout.** Build main interface: left panel (patient context), centre panel (document editor), top bar (recording controls + status). Implement: patient list dropdown, "Start Consultation" / "End Consultation" buttons, recording indicator, live transcript expandable section. | `gradio` 5.x, custom CSS (NHS Design System colour palette: `#003087` primary, `#005EB8` secondary, `#FFFFFF` background), `gradio.themes` | Functional UI layout with all panels and controls | UI renders in browser. All buttons are clickable. Panels are correctly positioned and responsive at 1280×720 and 1920×1080 |
| 14 | **Gradio UI (Part 2): data binding.** Connect UI to backend: clicking a patient triggers EHR agent → context panel populates. "Start Consultation" activates audio capture via JavaScript interop. "End Consultation" triggers document generation → draft letter appears in centre panel with inline editing. "Sign Off" button marks document as final. Export buttons (PDF, clipboard, FHIR DocumentReference). | `gradio` event handlers, `gr.State`, JavaScript interop for MediaRecorder | Fully interactive UI connected to backend | Complete end-to-end demo: select patient → see context → start recording → stop → draft letter appears → edit → sign off. All stages functional |
| 15 | **Integration testing (5 full scenarios).** Test 5 complete consultation scenarios end-to-end. Use pre-recorded synthetic audio clips (generated via TTS or self-recorded). Verify: correct transcription, accurate FHIR context retrieval, clinically appropriate generated letters, working inline editing, successful sign-off and export. | Pre-recorded WAV files, `pytest` for automated checks, manual verification | 5 passing end-to-end demo scenarios | All 5 scenarios complete without crash or error. Generated letters are clinically coherent for each patient |
| 16 | **Bug fixing + error handling.** Address all issues found in hour 15. Add: loading spinners, error messages for failed FHIR queries, timeout handling for model inference, graceful degradation if MedASR produces empty transcript, fallback if MedGemma 27B OOMs (reduce context length, retry). | Standard Python error handling, Gradio UI feedback components | Robust error-handled application | Re-run all 5 scenarios. Intentionally trigger 3 error conditions (empty audio, FHIR timeout, long transcript). All handled gracefully with user-visible feedback |

**DAY 3 — SUNDAY 15 FEBRUARY (Hours 17–24): Evaluation, Polish, Deployment**

| Hour | Task | Tools / Libraries | Deliverable | "Done" Criterion |
|---|---|---|---|---|
| 17 | **MedASR evaluation.** Measure WER on: (a) 20 synthetic medical dictation clips using `jiwer`, (b) 10 ambient conversation clips. Compare to Whisper large-v3 on same data. Document results. | `jiwer` 3.0.x, `openai-whisper` (for baseline comparison), custom test harness | WER comparison table: MedASR vs Whisper, dictation vs ambient | WER computed for all 30 clips. Results documented in `evaluation_report.md` |
| 18 | **EHR Agent evaluation.** Test FHIR retrieval accuracy on 20 synthetic patients against manually annotated "gold standard" context summaries. Measure: fact recall (% of relevant facts extracted), precision (% of extracted facts that are correct), hallucination rate (% of fabricated facts). | Custom evaluation script, 20 annotated gold standards | Agent accuracy report | Fact recall >85%, precision >90%, hallucination rate <10%. Results appended to `evaluation_report.md` |
| 19 | **Document generation evaluation + Ward Round mode.** Compute aggregate BLEU/ROUGE-L on full 50-sample test set. Implement Ward Round mode UI (sequential patient recording, progress note template instead of clinic letter). Test with 2 ward round scenarios. | `evaluate`, custom scripts, Gradio tab component | Ward Round mode functional + aggregate evaluation metrics | Ward Round tab generates progress notes. All metrics documented |
| 20 | **UI polish.** Apply NHS Design System aesthetics: colour palette, typography (Frutiger/Arial), spacing, accessibility (ARIA labels, contrast ratios ≥4.5:1). Add Clarke logo/branding. Responsive design check at 3 viewport sizes. Loading state animations. | CSS custom properties, Gradio theming API, SVG logo | Production-quality visual design | UI screenshots pass visual QA at 1280×720, 1920×1080, and 768×1024 (tablet). Lighthouse accessibility score ≥90 |
| 21 | **Pre-recorded demo preparation.** Record 3 polished demo audio clips (Mrs Thompson T2DM, Mr Okafor chest pain, Ms Patel asthma review). Each clip: 2–4 minutes, clear audio, realistic clinical dialogue. Save as 16kHz WAV. Verify MedASR transcribes accurately. | Audio recording (self/TTS), `ffmpeg` for format conversion | 3 demo-ready audio clips with verified transcripts | Each clip transcribes with <8% WER. Saved in `demo_data/` directory |
| 22 | **Hugging Face deployment.** Push application to public HF Space. Upload LoRA adapters to HF Hub as a separate model repository (tracing to `google/medgemma-27b-text-it`). Verify public access: anyone can visit the URL and interact. Test from a different browser/device. | HF Spaces CLI, `huggingface_hub` SDK, `git-lfs` | Live public demo URL + public LoRA adapter repo | External browser (incognito) can access demo, select a patient, play pre-recorded audio, and receive a generated letter |
| 23 | **Repository documentation.** Write comprehensive README.md: project description, architecture diagram, installation instructions, usage guide, model card, evaluation results, licence (Apache 2.0 for code, HAI-DEF terms for models). Annotate all source code files with docstrings and inline comments. | Markdown, standard Python docstrings | Documented public GitHub repository | README contains: architecture diagram, quickstart guide, evaluation table, licence info. All `.py` files have module-level docstrings |
| 24 | **Final verification + submission artefacts.** End-to-end smoke test of live demo. Verify: GitHub repo is public, HF Space is live, HF model repo with LoRA adapter is public. Create `submission_checklist.md` confirming all competition requirements met. | Manual testing, checklist | All 3 submission artefacts publicly accessible | GitHub repo public ✓, HF Space live ✓, HF model repo public ✓. Demo runs without errors from external device |

### 6.2 Complete Technology Stack

| Layer | Component | Specific Technology | Version / Detail |
|---|---|---|---|
| **Infrastructure** | GPU compute | Hugging Face Spaces | A100 40GB GPU (ZeroGPU or dedicated; fallback: A10G 24GB) |
| | Container base | Docker | `nvidia/cuda:12.4.1-runtime-ubuntu22.04` |
| | Runtime | Python | 3.11.x |
| **Backend** | Web framework | FastAPI | 0.109.x, served via `uvicorn` 0.27.x |
| | Async | Python asyncio | Built-in, for concurrent MedASR + EHR Agent execution |
| | WebSocket | `websockets` | 12.x, for real-time audio streaming and transcript return |
| **Frontend** | UI framework | Gradio | 5.x (latest), served within HF Space |
| | Audio capture | Browser MediaRecorder API | WebM/Opus codec → server-side conversion to 16kHz WAV |
| | Styling | Custom CSS | NHS Design System colour palette + Gradio theming API |
| **Audio processing** | Format conversion | `ffmpeg` | 7.x, for WebM→WAV transcoding |
| | Audio manipulation | `pydub` | 0.25.x, for resampling and channel conversion |
| | Audio analysis | `librosa` | 0.10.x, for waveform loading and preprocessing |
| **ASR model** | MedASR | `google/medasr` | 105M params, Conformer-based, via `transformers` AutoModelForSpeechSeq2Seq |
| **EHR Agent model** | MedGemma 1.5 4B IT | `google/medgemma-1.5-4b-it` | 4B params, 4-bit quantised via `bitsandbytes`, agent via `langgraph` 0.2.x |
| **Document generation model** | MedGemma 27B Text IT | `google/medgemma-27b-text-it` | 27B params, 4-bit NF4 quantised via `bitsandbytes` 0.44.x, double quantisation, `compute_dtype=bfloat16` |
| **ML framework** | Core | PyTorch | 2.4.x with CUDA 12.4 |
| | Model loading | `transformers` | 4.47.x (HuggingFace) |
| | Quantisation | `bitsandbytes` | 0.44.x (NF4 quantisation) |
| | Acceleration | `accelerate` | 1.2.x (device mapping) |
| **Fine-tuning** | LoRA framework | `peft` | 0.13.x (Parameter-Efficient Fine-Tuning) |
| | Training | `trl` (SFTTrainer) | 0.12.x |
| | Dataset loading | `datasets` | 3.2.x (HuggingFace) |
| | Experiment tracking | `wandb` | 0.18.x (Weights & Biases) |
| **FHIR** | Server | HAPI FHIR | v7.4, Docker container, FHIR R4 |
| | Client | `httpx` | 0.27.x (async HTTP for FHIR REST API calls) |
| | Data generation | Synthea | v3.3.0, configured with UK module (names, NHS numbers, mmol/L units, BNF drugs) |
| **Prompt engineering** | Template engine | `jinja2` | 3.1.x, for structured prompt assembly |
| **Evaluation** | WER | `jiwer` | 3.0.x |
| | Text similarity | `rouge_score`, `sacrebleu` | Latest stable |
| | ASR baseline | `openai-whisper` | large-v3 (for comparison only) |
| **Version control** | Repository | GitHub | Public repository, Apache 2.0 licence |
| **Model hosting** | LoRA adapter | Hugging Face Hub | Public model repo, tracing to `google/medgemma-27b-text-it` |
| **Document export** | PDF generation | `reportlab` | 4.2.x, for clinic letter PDF export |

### 6.3 Fine-Tuning Strategy

**Model 1: MedGemma 27B Text-Only — NHS Clinical Letter Generation (Primary fine-tuning target)**

- **Objective:** Adapt MedGemma 27B from general medical Q&A to structured NHS clinical document generation from (transcript, FHIR context) input pairs.

- **Data generation:**
  1. Select 50 diverse Synthea patients spanning: diabetes, COPD, heart failure, CKD, hypertension, cancer follow-up, mental health, orthopaedic, paediatric, obstetric scenarios.
  2. For each patient, generate 5 training triplets using Claude 3.5 Sonnet API (total: 250 training + 50 held-out test):
     - **Input 1:** Simulated clinician-patient conversation transcript (~500–1,500 words, naturalistic dialogue including interruptions, repetition, non-medical small talk)
     - **Input 2:** FHIR context JSON (extracted from Synthea patient data: demographics, conditions, medications, labs, allergies)
     - **Output:** Reference NHS-format clinic letter following Royal College of Physicians guidelines: date, addressee (GP), patient demographics, reason for consultation, history of presenting complaint, relevant PMH, examination findings, investigation results (with actual values from FHIR context), assessment, plan, follow-up.
  3. Manually review 40 triplets (20 training, 20 test) for clinical accuracy, correct FHIR value usage, and NHS format compliance. Revise and re-generate any with errors.
  
- **Dataset format:** JSONL, one example per line. Each line: `{"messages": [{"role": "system", "content": "<NHS_LETTER_INSTRUCTIONS>"}, {"role": "user", "content": "<TRANSCRIPT>\n\n<FHIR_CONTEXT>"}, {"role": "assistant", "content": "<REFERENCE_LETTER>"}]}`

- **Method:** QLoRA (Quantised Low-Rank Adaptation)
  - **Base model:** `google/medgemma-27b-text-it`, loaded in 4-bit NF4 quantisation with double quantisation
  - **LoRA targets:** `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` (all attention + MLP projections)
  - **LoRA rank:** 16
  - **LoRA alpha:** 32 (scaling factor = alpha/rank = 2.0)
  - **LoRA dropout:** 0.05
  - **Optimizer:** paged_adamw_8bit
  - **Learning rate:** 2e-4
  - **LR scheduler:** cosine with warmup
  - **Warmup ratio:** 0.03 (≈2 warmup steps for 250 examples × 3 epochs / batch)
  - **Per-device batch size:** 2
  - **Gradient accumulation steps:** 8 (effective batch size: 16)
  - **Max sequence length:** 4,096 tokens
  - **Epochs:** 3
  - **Mixed precision:** bf16

- **Hardware:** Single A100 40GB GPU (same as inference; LoRA adapters fit in remaining VRAM after 4-bit base model).

- **Duration estimate:** ~2.5 hours for 250 examples × 3 epochs at batch size 2 with gradient accumulation of 8, max_seq_length 4096 on A100 40GB. Based on comparable LoRA fine-tuning benchmarks for 27B models.

- **Output:** LoRA adapter checkpoint (~200–500MB), uploaded to Hugging Face Hub as a public model tracing to `google/medgemma-27b-text-it`.

**Model 2: MedASR — NHS-Accented Medical Speech (Stretch goal, hours 19–20 if evaluation results indicate need)**

- **Rationale:** Only pursued if hour-17 evaluation shows MedASR WER on synthetic NHS-accented audio exceeds 10%. If base MedASR WER is acceptable (<10%), document this as a production requirement and proceed with base model.
- **Data:** 100–500 labelled medical utterances with UK/international accents. For the demo, these can be self-recorded or sourced from open medical speech datasets.
- **Method:** LoRA fine-tuning following Google's published MedASR fine-tuning notebook. LoRA rank 8, learning rate 1e-4, 5 epochs.
- **Duration:** ~1 hour on A100.
- **Fallback (if not pursued):** Document base MedASR performance on NHS-accented audio in the evaluation report. Note this as a production fine-tuning requirement.

### 6.4 Model Performance Evaluation Plan

| Model | Metric | Test Set | Baseline | Target | Evaluation Method |
|---|---|---|---|---|---|
| **MedASR** | Word Error Rate (WER) | 20 medical dictation clips (synthetic, clear audio, US-accent) + 10 ambient conversation clips (synthetic, multi-speaker, UK-accent) | Whisper large-v3 WER on identical audio | MedASR WER < Whisper WER on dictation (expect ≥58% relative improvement per published benchmarks); MedASR WER < 10% absolute on ambient clips | `jiwer` library; manual ground-truth transcripts for each clip |
| **MedGemma 4B (EHR Agent)** | Fact recall, precision, hallucination rate | 20 synthetic patient records with manually annotated gold-standard context summaries (each containing 15–25 clinically relevant facts) | Naive FHIR dump (return all resources without summarisation or filtering) | Fact recall >85%, precision >90%, hallucination rate <10% | Custom script comparing agent JSON output to gold-standard annotations; 2 reviewers for 10 disagreement cases |
| **MedGemma 27B (Document Gen, base)** | BLEU, ROUGE-L | 50 held-out (transcript, context, letter) triplets | N/A (this is the baseline) | Establish baseline scores | `sacrebleu`, `rouge_score` |
| **MedGemma 27B (Document Gen, fine-tuned)** | BLEU, ROUGE-L, clinical accuracy | Same 50 held-out triplets | Base MedGemma 27B scores (from row above) | BLEU improvement ≥5 points; ROUGE-L improvement ≥3 points; manual review confirms improved NHS format compliance in ≥8/10 sampled letters | Automated metrics + manual clinical review of 10 randomly sampled letters by team clinician |
| **End-to-end pipeline** | Latency (time from "End Consultation" to draft letter display) | 5 full demo scenarios | Manual documentation time (~15 min per clinician survey) | <60 seconds from click to rendered letter | Stopwatch measurement across 5 trials; mean and max recorded |
| **End-to-end pipeline** | Clinical coherence (manual) | 5 generated letters from demo scenarios | N/A (qualitative) | All 5 letters are clinically coherent, factually consistent with FHIR data, and follow NHS letter structure | Manual review by team clinician using a 5-point rubric: format compliance, clinical accuracy, FHIR value correctness, appropriate plan, readability |

---

## SECTION 7: DEPLOYMENT & DEMO SPECIFICATION

### 7.1 Live Demo Scenario

The demo shows a complete consultation with a synthetic NHS patient, designed to demonstrate every stage of Clarke's agentic pipeline in under 3 minutes. A judge watching the video will see exactly this:

**Screen 1 — Dashboard (0:00–0:15)**

Clarke opens in a web browser showing a mock clinic list for "Dr. Sarah Chen, Diabetes & Endocrinology." Five patients are listed with appointment times and one-line summaries. The first patient is highlighted:

> **Mrs. Margaret Thompson** | 67F | 14:00 | Follow-up — Type 2 Diabetes, rising HbA1c

The clinician (or narrator) clicks on Mrs. Thompson's name.

**Screen 2 — Patient Context Loading (0:15–0:25)**

A brief loading animation plays (3–5 seconds) as Clarke's EHR Agent (MedGemma 4B) queries the FHIR server. The Patient Context panel on the left populates with structured data:

- **Diagnoses:** Type 2 Diabetes Mellitus (2019), Hypertension (2017), CKD Stage 3a (2023)
- **Medications:** Metformin 1g BD, Ramipril 5mg OD, Atorvastatin 20mg OD
- **Allergies:** ⚠ Penicillin (anaphylaxis)
- **Recent Labs:** HbA1c **55** mmol/mol ↑ (was 48 in Jun 2025) · eGFR **52** mL/min ↓ (was 58) · Creatinine **98** μmol/L
- **Flag:** "⚠ HbA1c rising trend over 6 months — consider treatment escalation"

**Screen 3 — Live Consultation (0:25–1:30)**

The clinician clicks **"Start Consultation."** A red recording indicator appears. A pre-recorded synthetic audio clip plays (~60 seconds, ~250 words):

> Doctor: "Hello Mrs. Thompson, good to see you again. How have you been since we last met?"
> Patient: "Not too bad doctor, but I've been a bit more tired lately and I'm worried about my sugar levels..."
> [Conversation covers: fatigue symptoms, dietary adherence, discussion of HbA1c rising from 48 to 55, explanation that metformin alone isn't enough, shared decision to start gliclazide, discussion of hypoglycaemia risk, plan for repeat HbA1c in 3 months]

The Live Transcript panel shows MedASR's real-time text appearing as the audio plays, demonstrating the streaming transcription.

**Screen 4 — Document Generation (1:30–1:50)**

The clinician clicks **"End Consultation."** The recording stops. A progress indicator appears: "Generating clinical letter..." (15–20 seconds). During this time, a subtle animation shows the three pipeline stages: "Transcribing... → Retrieving context... → Drafting letter..."

**Screen 5 — Draft Clinic Letter (1:50–2:30)**

A structured NHS clinic letter appears in the centre panel:

> **[NHS Trust Header]**
> **Date:** 13 February 2026
> **NHS Number:** 943 476 5829
>
> Dr. R. Patel
> Riverside Medical Centre
> 45 High Street, London SE1 2AB
>
> **Re: Mrs. Margaret Thompson, DOB 14/03/1958**
>
> Dear Dr. Patel,
>
> Thank you for asking me to review Mrs. Thompson in the Diabetes clinic today.
>
> **History of presenting complaint:** Mrs. Thompson reports increasing fatigue over the past 2–3 months. She has been adherent to dietary advice but has found it difficult to reduce her carbohydrate intake further. She denies polyuria, polydipsia, or weight loss.
>
> **Investigation results:** Her HbA1c has risen from **48 mmol/mol** (June 2025) to **55 mmol/mol** (January 2026), indicating worsening glycaemic control despite metformin monotherapy. Her renal function shows eGFR **52 mL/min** (previously 58), consistent with stable CKD Stage 3a. Creatinine is **98 μmol/L**.
>
> **Assessment and plan:** Given the rising HbA1c on maximum-dose metformin, I have discussed treatment escalation with Mrs. Thompson and we have agreed to commence **gliclazide 40mg once daily**. I have counselled her regarding the risk of hypoglycaemia and provided written patient information. Please arrange a repeat HbA1c in **3 months** and review her renal function at that time.
>
> **Current medications:** Metformin 1g BD, Gliclazide 40mg OD (NEW), Ramipril 5mg OD, Atorvastatin 20mg OD.
>
> Yours sincerely,
> Dr. S. Chen, Consultant Diabetologist

The narrator points out: (a) investigation values are hyperlinked to their FHIR source records, (b) the letter includes both conversation content AND FHIR-sourced data, (c) the allergy is preserved.

**Screen 6 — Edit and Sign Off (2:30–2:50)**

The clinician edits one line (e.g., adding "She is tolerating metformin well with no GI side effects" — demonstrating inline editing). Then clicks **"Sign Off."** The document status changes to "✓ Approved." Export buttons appear: PDF, Copy to Clipboard, FHIR DocumentReference.

**Screen 7 — Closing (2:50–3:00)**

Brief closing card showing: "Clarke: 3 HAI-DEF models. 1 pipeline. Zero patient data leaves the building." with the project URL.

**Synthetic data used:** 50 Synthea-generated UK-style patients loaded into HAPI FHIR server. 3 pre-recorded audio clips for demo scenarios (Mrs. Thompson — diabetes; Mr. Okafor — chest pain follow-up; Ms. Patel — asthma review). Audio clips are 60–90 seconds, recorded in clear studio conditions at 16kHz WAV.

### 7.2 Top 5 Deployment Challenges and Mitigations

| # | Challenge | Specific Mitigation | Evidence / Precedent |
|---|---|---|---|
| 1 | **GPU hardware cost for NHS trusts** | MedGemma 4B runs on a single consumer GPU (RTX 4060 8GB, ~£300). MedGemma 27B quantised to 4-bit runs on a single A100 40GB or two A10G 24GB GPUs. NHS trusts already procure similar hardware for PACS imaging workstations. Capital cost: £5,000–£15,000 per trust (one-time), versus >£2M/year for Heidi Health licensing across a trust's doctors at $99/clinician/month. | NHS PACS infrastructure includes GPU workstations. NHS Digital recommends GPU-enabled infrastructure for AI workloads. |
| 2 | **NHS accent diversity and MedASR accuracy** | Fine-tune MedASR with LoRA on NHS-accented audio. Google's published fine-tuning notebook provides the methodology. MedASR's Conformer architecture handles accent variation better than RNN-based ASRs. For production: each trust collects 100–500 de-identified audio samples from its own clinicians for local LoRA fine-tuning (~1 hour compute). | MedASR was trained on ~5,000 hours of diverse physician dictations. LoRA fine-tuning is computationally cheap (minutes to hours). |
| 3 | **FHIR API availability across NHS trusts** | Demo uses HAPI FHIR with Synthea data. Production: NHS England's Interoperability Standards mandate FHIR R4 API exposure. EMIS, SystmOne, and Cerner/Oracle Health increasingly offer FHIR endpoints. Clarke degrades gracefully — if no FHIR API is available, it operates in "documentation-only" mode (ambient scribe without EHR context), still valuable. | NHS England's NHS England Digital Interoperability Programme (2024–2025) mandates FHIR for data sharing. The eDischarge Summary Standard (PRSB, updated January 2026) mandates structured discharge data transfer. |
| 4 | **Clinical safety of AI-generated documents** | Clarke is a drafting tool, not an autonomous documentation system. Every document requires mandatory clinician review and sign-off before entering the medical record. FHIR-sourced values are hyperlinked to source records for verification. Discrepancy flags (e.g., allergy mismatch between conversation and record) are prominently displayed in red. | Google's HAI-DEF Terms of Use explicitly state model outputs require independent professional verification. Mass General Brigham's ambient AI programme (3,000+ providers) uses the same review-before-filing workflow. |
| 5 | **Information governance and regulatory status** | All processing is local — no external data transmission. Open-source code is fully auditable by trust IG teams. Clarke is positioned as a clinical decision support tool (not a regulated medical device), consistent with MHRA guidance on software as a medical device. A Data Protection Impact Assessment (DPIA) would be completed per trust. | NHS England published guidance on AI scribes in health settings (April 2025). Open-source audit trail addresses NHS IG requirement for transparency. |

### 7.3 Production Deployment Path

**Phase 1 — Single-trust pilot (months 0–6)**

- **Setup:** Deploy Clarke on a dedicated GPU server (A100 or 2×A10G) within the trust's on-premise data centre or private cloud (e.g., NHS-approved Azure/AWS tenancy). Dockerised deployment using `docker-compose` with three services: Clarke application, HAPI FHIR proxy, GPU model server.
- **Scope:** 10–20 clinicians across 2–3 specialties (e.g., diabetes outpatients, general medicine ward round, GP training practice). Selected for diversity of documentation types.
- **Integration:** Connect FHIR proxy to the trust's EHR (EMIS/SystmOne/Cerner) via existing FHIR R4 endpoints. Read-only access — Clarke does not write to the EHR in Phase 1.
- **Measurement:** Prospective time-motion study comparing documentation time with vs. without Clarke. Pre-post burnout survey using validated instruments (MBI or Mini-Z). Letter quality audit: completeness, accuracy, NHS format compliance. Clinician satisfaction (System Usability Scale).
- **Governance:** DPIA completed. Information governance approval from trust Caldicott Guardian. Clinical safety case per DCB0129 standard. Ethics approval if results are intended for publication.

**Phase 2 — Trust-wide rollout (months 6–12)**

- Expand to all clinicians in the pilot trust. Fine-tune MedASR on the trust's collected audio data for accent optimisation. Integrate EHR write-back (with appropriate clinical safety controls) so signed-off letters can be filed directly into the patient record.
- Begin second-trust pilot to demonstrate transferability.

**Phase 3 — Multi-trust deployment (months 12–24)**

- Package Clarke as a `docker-compose` deployment kit with comprehensive setup documentation.
- Publish on NHS App Store / Digital Marketplace for trust procurement teams.
- Work with NHS England's AI and Digital Regulation programme for national endorsement.
- Share specialty-specific LoRA adapters (e.g., cardiology, psychiatry, paediatrics) on Hugging Face Hub.

**Phase 4 — Ongoing open-source development**

- Community-driven improvement via GitHub contributions. Trust-specific LoRA adapters (accent, specialty, local conventions) shared on Hugging Face Hub. Regular model updates as Google releases new MedGemma and MedASR versions.

---

## SECTION 8: REFERENCES

1. Arab S, Chhatwal K, Hargreaves T, et al. Time Allocation in Clinical Training (TACT): national study reveals Resident Doctors spend four hours on admin for every hour with patients. *QJM: An International Journal of Medicine*. 2025;118(10):753. doi:10.1093/qjmed/hcaf141.

2. Olson KD, Meeker D, Troup M, et al. Use of Ambient AI Scribes to Reduce Administrative Burden and Professional Burnout. *JAMA Network Open*. 2025;8(10):e2534976. doi:10.1001/jamanetworkopen.2025.34976.

3. Pearlman K, Wan W, Shah S, Laiteerapong N. Use of an AI Scribe and Electronic Health Record Efficiency. *JAMA Network Open*. 2025;8(10):e2537000. doi:10.1001/jamanetworkopen.2025.37000.

4. You JG, Landman A, Ting DY, et al. Ambient Documentation Technology in Clinician Experience of Documentation Burden and Burnout. *JAMA Network Open*. 2025. doi:10.1001/jamanetworkopen.2025.28056.

5. Moura LMVR, Mishuris R, Metlay JP, et al. Hybrid Ambient Clinical Documentation and Physician Performance: Work Outside of Work, Documentation Delay, and Financial Productivity. *Journal of General Internal Medicine*. 2025. doi:10.1007/s11606-025-09979-5.

6. NHS Digital. NHS Workforce Statistics — August 2025. Published November 2025. https://digital.nhs.uk/data-and-information/publications/statistical/nhs-workforce-statistics/august-2025.

7. NHS Digital. General Practice Workforce — 31 December 2025. https://digital.nhs.uk/data-and-information/publications/statistical/general-and-personal-medical-services/31-december-2025.

8. BMA. NHS Backlog Data Analysis. Accessed February 2026. https://www.bma.org.uk/advice-and-support/nhs-delivery-and-workforce/pressures/nhs-backlog-data-analysis.

9. BMA. Medical Staffing in the NHS — Data Analysis. Accessed February 2026. https://www.bma.org.uk/advice-and-support/nhs-delivery-and-workforce/workforce/medical-staffing-in-the-nhs.

10. GMC. National Training Survey 2025. Published July 2025. Referenced via NHS Employers: https://www.nhsemployers.org/news/gmc-national-training-survey-2025.

11. Google Research. Next generation medical image interpretation with MedGemma 1.5 and medical speech to text with MedASR. Published January 2026. https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/.

12. Google. MedASR Model Card. Hugging Face. https://huggingface.co/google/medasr.

13. Google. MedASR Developer Documentation. https://developers.google.com/health-ai-developer-foundations/medasr.

14. Google. MedGemma Technical Report. arXiv:2507.05201.

15. Google. Health AI Developer Foundations (HAI-DEF) Technical Report. arXiv:2411.15128.

16. King's Fund. Waiting Times for Elective (Non-Urgent) Treatment: Referral to Treatment (RTT). Updated December 2025. https://www.kingsfund.org.uk/insight-and-analysis/data-and-charts/waiting-times-non-urgent-treatment.

17. MedGamma Clinician Survey. 47 responses from NHS and healthcare clinicians. Collected January 16 – February 8, 2026. Internal document.

18. TechFundingNews. Heidi raises $65M to scale its AI scribe across global health systems. October 2025. https://techfundingnews.com/heidi-ai-care-partner-65m-series-b-global-expansion/.

19. Mass General Brigham. Ambient Documentation Technologies Reduce Physician Burnout and Restore 'Joy' in Medicine. Press release, August 2025. https://www.massgeneralbrigham.org/en/about/newsroom/press-releases/ambient-documentation-technologies-reduce-physician-burnout.

20. Medscape UK. Medscape UK Survey: Burnout Hits Doctors Amid NHS Pressures. June 2025.

21. iatroX. The rise of AI medical scribes in UK primary care. August 2025. https://www.iatrox.com/blog/ai-medical-scribes-uk-gp-guide-tortus-accurx-heidi.

22. Burnett S, Franklin BD, Moorthy K, et al. Missing Clinical Information in NHS hospital outpatient clinics: prevalence, causes and effects on patient care. *BMC Health Services Research*. 2011;11:114. doi:10.1186/1472-6963-11-114.

23. NHS Resolution. Annual Report and Accounts 2024 to 2025. Published July 2025. https://www.gov.uk/government/publications/nhs-resolution-annual-report-and-accounts-2024-to-2025.

24. NHS England. NHS Patient Safety Strategy — Progress Update — April 2025. https://www.england.nhs.uk/patient-safety/the-nhs-patient-safety-strategy/.

25. PRSB. eDischarge Summary Standard. Updated January 2026. https://theprsb.org/standards/edischargesummary/.

26. NHS Providers. NHS Digital Workforce Statistics — November 2025. https://nhsproviders.org/resources/nhs-digital-workforce-statistics-november-2025.

---

*Document prepared for Clarke PRD generation — Version 2.0 — February 2026*
