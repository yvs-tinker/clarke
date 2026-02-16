---
title: Clarke
emoji: 🩺
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 7860
---

# Clarke

**AI-powered NHS clinic letter generation — from consultation audio to structured clinical document in under 60 seconds.**

Clarke is an ambient clinical documentation system that converts doctor–patient audio consultations into structured NHS clinic letters. It coordinates three [HAI-DEF](https://goo.gle/hai-def) models as autonomous agents in a unified agentic pipeline: medical speech recognition, EHR context retrieval via FHIR, and context-enriched document generation.

Built for the [MedGemma Impact Challenge](https://www.kaggle.com/competitions/medgemma-impact-challenge) on Kaggle, targeting the **Agentic Workflow Prize**.

---

## The Problem

NHS doctors spend 73% of their working time on non-patient-facing tasks, with only 17.9% on direct patient care [Arab et al., QJM 2025; TACT study, 137 doctors, 7 months] - that's four hours on administration for every one hour with patients. Documentation alone consumes "~15 minutes per patient" encounter — across a typical 10–12 patient clinic session, that is 2.5–3 hours of writing per session [Clinician survey, n=47]. Multiply this across 190,200 FTE doctors in England [NHS Digital, Aug 2025], and the scale becomes clear: 7,248 unfilled medical vacancies [NHS Digital, Sep 2025], 7.31 million patients on the waiting list [BMA/King's Fund, Nov 2025], and 61% of trainees at moderate-to-high burnout risk [GMC NTS, 2025].
Ambient AI scribes have shown promise — reducing clinician burnout from 51.9% to 38.8% within 30 days [Olson et al., JAMA Netw Open 2025]. But every existing solution (Heidi Health, DAX Copilot, Tortus) generates documents from conversation audio alone. None retrieves EHR context - clinicians must still manually add lab values, medication lists, and allergy checks. All are cloud-dependent, closed-source, and costly: Heidi alone would cost £226M/year at NHS scale.
Clarke closes both gaps: ambient documentation fused with intelligent EHR retrieval, fully open-source, designed for local deployment.

---

## Architecture

Clarke orchestrates three HAI-DEF models in a five-stage agentic workflow. Each model operates as an autonomous agent, making its own decisions about what to process, retrieve, or generate:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLARKE PIPELINE                          │
│                                                                 │
│   ┌─────────────┐                                               │
│   │  Audio Input │  Upload or record consultation audio         │
│   └──────┬──────┘                                               │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────────────────────────────────┐                   │
│   │  ① MedASR  (google/medasr)              │                   │
│   │     Medical speech recognition agent    │                   │
│   │     Audio → clinical transcript         │                   │
│   └──────┬──────────────────────────────────┘                   │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────────────────────────────────┐    ┌────────────┐ │
│   │  ② MedGemma 4B IT                      │◄──►│ FHIR Server│ │
│   │     (google/medgemma-1.5-4b-it)         │    │ Patient    │ │
│   │     EHR context retrieval agent         │    │ records    │ │
│   │     Patient ID → structured context     │    └────────────┘ │
│   └──────┬──────────────────────────────────┘                   │
│          │  transcript + patient context                        │
│          ▼                                                      │
│   ┌─────────────────────────────────────────┐                   │
│   │  ③ MedGemma 27B Text-IT                │                   │
│   │     (google/medgemma-27b-text-it)       │                   │
│   │     Document generation agent           │                   │
│   │     Transcript + context → NHS letter   │                   │
│   └──────┬──────────────────────────────────┘                   │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────┐                                               │
│   │  Draft Letter│  Clinician review, edit, and sign-off       │
│   └─────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

**Why three models, not one?** Each HAI-DEF model contributes a distinct capability that no single model can replicate. MedASR provides medical-domain speech recognition with 58–82% fewer errors than general-purpose alternatives. MedGemma 4B understands FHIR resources natively, retrieving and synthesising relevant patient history. MedGemma 27B generates clinically accurate prose grounded in both the conversation and the medical record. The pipeline produces documents that reference actual lab values, include current medication lists, and cross-check for consistency — something no conversation-only scribe can achieve.

---

## Features

- **End-to-end ambient documentation** — six-screen clinician workflow from patient selection through letter sign-off.
- **Three-model agentic pipeline** — MedASR, MedGemma 4B, and MedGemma 27B operating as coordinated autonomous agents.
- **FHIR-backed context enrichment** — retrieves patient demographics, active conditions, medications, lab results, allergies, and diagnostic reports via HL7 FHIR.
- **Structured NHS clinic letter output** — generated documents follow standard NHS letter format with appropriate clinical structure.
- **Privacy-preserving architecture** — designed for local deployment; no patient data leaves the hospital network.
- **Deterministic fallback paths** — graceful degradation ensures reliability when individual model components encounter issues.
- **Mock-safe local development** — full pipeline runs without GPU access or gated model downloads using built-in mock services.

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/yvs-tinker/clarke.git
cd clarke
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run in mock mode (no GPU required)

```bash
USE_MOCK_FHIR=true MEDASR_MODEL_ID=mock MEDGEMMA_4B_MODEL_ID=mock MEDGEMMA_27B_MODEL_ID=mock python3 app.py
```

Open [http://localhost:7860](http://localhost:7860) in your browser.

### Running with real models (requires GPU + HF access)

Create a `.env` file in the project root:

```bash
MEDASR_MODEL_ID=google/medasr
MEDGEMMA_4B_MODEL_ID=google/medgemma-1.5-4b-it
MEDGEMMA_27B_MODEL_ID=google/medgemma-27b-text-it
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
FHIR_BASE_URL=http://localhost:8080/fhir
APP_HOST=0.0.0.0
APP_PORT=7860
```

Then launch as above. Requires an NVIDIA A100 (or equivalent) for the full three-model pipeline.

---

## Models

Clarke uses three models from Google's [Health AI Developer Foundations (HAI-DEF)](https://goo.gle/hai-def) collection:

| Role | Model | Description |
|---|---|---|
| Medical speech recognition | [`google/medasr`](https://huggingface.co/google/medasr) | Domain-specific ASR optimised for medical terminology, achieving 58–82% relative WER improvement over general-purpose models. |
| EHR context retrieval | [`google/medgemma-1.5-4b-it`](https://huggingface.co/google/medgemma-1.5-4b-it) | Instruction-tuned multimodal model with native understanding of clinical data and FHIR resources. |
| Document generation | [`google/medgemma-27b-text-it`](https://huggingface.co/google/medgemma-27b-text-it) | Large-scale text generation model for producing clinically accurate, structured medical documents. |

---

## Repository Structure

```
clarke/
├── app.py                    # Application entry point (FastAPI + Gradio)
├── backend/
│   ├── api.py                # FastAPI REST endpoints
│   ├── orchestrator.py       # Pipeline coordinator
│   ├── config.py             # Environment and settings
│   ├── schemas.py            # Pydantic data models
│   ├── models/
│   │   ├── medasr.py         # MedASR transcription wrapper
│   │   ├── ehr_agent.py      # MedGemma 4B EHR retrieval agent
│   │   └── doc_generator.py  # MedGemma 27B letter generation agent
│   ├── fhir/
│   │   ├── client.py         # FHIR server client
│   │   ├── queries.py        # FHIR resource queries
│   │   ├── tools.py          # Agent tool definitions
│   │   └── mock_api.py       # Mock FHIR server for local development
│   └── prompts/              # Prompt templates (Jinja2)
├── frontend/
│   ├── ui.py                 # Gradio interface builder
│   ├── components.py         # UI screen components
│   ├── state.py              # Session state management
│   └── assets/               # CSS, logo, static files
├── data/                     # Demo audio, transcripts, synthetic FHIR bundles
├── evaluation/               # WER, fact recall, BLEU/ROUGE-L eval scripts
├── finetuning/               # LoRA training scripts and adapter outputs
└── tests/                    # Unit, integration, and end-to-end tests
```

---

## Links

| Resource | URL |
|---|---|
| **Live demo** | [yashvshetty-clarke.hf.space](https://yashvshetty-clarke.hf.space) |
| **Source code** | [github.com/yvs-tinker/clarke](https://github.com/yvs-tinker/clarke) |

---

## Licence

- **Code:** [Apache 2.0](LICENSE)
- **Models:** Subject to [HAI-DEF Terms of Use](https://developers.google.com/health-ai-developer-foundations/terms) and Hugging Face gating requirements.

---

## Acknowledgements

- [MedGemma Impact Challenge](https://www.kaggle.com/competitions/medgemma-impact-challenge) — Google Health AI
- [HAI-DEF](https://goo.gle/hai-def) — Health AI Developer Foundations model releases
- [Synthea](https://synthetichealth.github.io/synthea/) — Synthetic patient data generation
- [HAPI FHIR](https://hapifhir.io/) — FHIR server ecosystem and tooling
