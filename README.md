---
title: Clarke
emoji: 🩺
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 7860
---

# Clarke

**AI-powered NHS clinic letter generation: from consultation audio to structured clinical document in under 60 seconds.**

Clarke is an ambient clinical documentation system that converts doctor-patient audio consultations into structured NHS clinic letters. It coordinates three [HAI-DEF](https://goo.gle/hai-def) models as autonomous agents in a unified agentic pipeline: medical speech recognition, EHR context retrieval via FHIR, and context-enriched document generation.

Built for the [MedGemma Impact Challenge](https://www.kaggle.com/competitions/medgemma-impact-challenge) on Kaggle, targeting the **Agentic Workflow Prize**.

| Resource | Link |
|----------|------|
| Live demo | [yashvshetty-clarke.hf.space](https://yashvshetty-clarke.hf.space) |
| Source code | [github.com/yvs-tinker/clarke](https://github.com/yvs-tinker/clarke) |
| Evaluation report | [evaluation/EVALUATION.md](evaluation/EVALUATION.md) |
| LoRA adapter | [yashvshetty/clarke-medgemma-27b-lora](https://huggingface.co/yashvshetty/clarke-medgemma-27b-lora) |
| Demo video | *Coming soon* |

---

## Results

Clarke was evaluated across five NHS outpatient consultations spanning endocrine, cardiology, respiratory, heart failure, and mental health. Full methodology and per-patient breakdowns are in the [evaluation report](evaluation/EVALUATION.md).

| Component | Metric | Score |
|-----------|--------|-------|
| MedASR (speech-to-text) | Word Error Rate | 13.28% across 1,438 words |
| EHR Agent (record retrieval) | Fact Recall | 100% (70/70 facts retrieved) |
| EHR Agent | Precision | 98.6% (1 hallucination in 71 facts) |
| Document Generation (base) | BLEU-1 / ROUGE-L | 0.54 / 0.44 |
| Document Generation (after QLoRA) | BLEU-1 / ROUGE-L | **0.71 / 0.47** (+31% BLEU-1) |

QLoRA fine-tuning on just 5 gold-standard NHS clinic letters improved lexical accuracy by 31%, trained in 15 minutes on a single A100 GPU. The adapter is published at [`yashvshetty/clarke-medgemma-27b-lora`](https://huggingface.co/yashvshetty/clarke-medgemma-27b-lora).

---

## The Problem

NHS doctors spend 73% of their working time on non-patient-facing tasks, with only 17.9% on direct patient care (Arab et al., QJM 2025; TACT study, 137 doctors, 7 months). Documentation alone consumes approximately 15 minutes per patient encounter. Across a typical 10-12 patient clinic, that is 2.5-3 hours of writing per session (clinician survey, n=47). At the scale of 190,200 FTE doctors in England (NHS Digital, Aug 2025), the impact compounds: 7,248 unfilled medical vacancies, 7.31 million patients on the waiting list (BMA/King's Fund, Nov 2025), and 61% of trainees at moderate-to-high burnout risk (GMC NTS, 2025).

Ambient AI scribes have shown promise, reducing clinician burnout from 51.9% to 38.8% within 30 days (Olson et al., JAMA Netw Open 2025). But every existing solution (Heidi Health, DAX Copilot, Tortus) generates documents from conversation audio alone. None retrieves EHR context, meaning clinicians must still manually add lab values, medication lists, and allergy checks. All are cloud-dependent, closed-source, and costly: Heidi alone would cost an estimated 226M GBP/year at NHS scale.

Clarke closes both gaps: ambient documentation fused with intelligent EHR retrieval, fully open-source, designed for local deployment.

### Clinician Validation

A 47-respondent clinician survey confirmed the problem. Respondents reported spending substantial time on documentation, identified clinical letter writing as the most time-consuming task, and expressed strong interest in AI-assisted documentation tools with EHR integration.

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
│   │  1. MedASR  (google/medasr)             │                   │
│   │     Medical speech recognition agent    │                   │
│   │     Audio -> clinical transcript        │                   │
│   └──────┬──────────────────────────────────┘                   │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────────────────────────────────┐    ┌────────────┐ │
│   │  2. MedGemma 4B IT                      │<-->│ FHIR Server│ │
│   │     (google/medgemma-1.5-4b-it)         │    │ Patient    │ │
│   │     EHR context retrieval agent         │    │ records    │ │
│   │     Patient ID -> structured context    │    └────────────┘ │
│   └──────┬──────────────────────────────────┘                   │
│          │  transcript + patient context                        │
│          ▼                                                      │
│   ┌─────────────────────────────────────────┐                   │
│   │  3. MedGemma 27B Text-IT                │                   │
│   │     (google/medgemma-27b-text-it)       │                   │
│   │     Document generation agent           │                   │
│   │     Transcript + context -> NHS letter  │                   │
│   └──────┬──────────────────────────────────┘                   │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────┐                                               │
│   │  Draft Letter│  Clinician review, edit, and sign-off       │
│   └─────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

**Why three models, not one?** Each HAI-DEF model contributes a distinct capability that no single model can replicate. MedASR provides medical-domain speech recognition optimised for clinical terminology. MedGemma 4B understands FHIR resources natively, retrieving and synthesising relevant patient history. MedGemma 27B generates clinically accurate prose grounded in both the conversation and the medical record. The pipeline produces documents that reference actual lab values, include current medication lists, and cross-check for consistency. No conversation-only scribe can achieve this.

---

## Features

- **End-to-end ambient documentation** from patient selection through letter sign-off.
- **Three-model agentic pipeline** with MedASR, MedGemma 4B, and MedGemma 27B operating as coordinated agents.
- **FHIR-backed context enrichment** retrieving demographics, conditions, medications, lab results, allergies, and diagnostic reports.
- **Structured NHS clinic letter output** following standard clinical correspondence format.
- **QLoRA fine-tuning** with a published LoRA adapter achieving 31% BLEU-1 improvement.
- **Privacy-preserving architecture** designed for local deployment; no patient data leaves the hospital network.
- **Deterministic safety architecture** in the EHR agent ensures 100% fact recall by design.
- **Human-in-the-loop review** with mandatory clinician sign-off before any document is exported.
- **Mock-safe local development** enabling the full pipeline to run without GPU or gated model access.

---

## Models

Clarke uses three models from Google's [Health AI Developer Foundations (HAI-DEF)](https://goo.gle/hai-def) collection:

| Role | Model | What it does |
|------|-------|-------------|
| Speech recognition | [`google/medasr`](https://huggingface.co/google/medasr) | Converts consultation audio to text with medical vocabulary optimisation |
| EHR retrieval | [`google/medgemma-1.5-4b-it`](https://huggingface.co/google/medgemma-1.5-4b-it) | Queries FHIR records and synthesises structured patient context |
| Document generation | [`google/medgemma-27b-text-it`](https://huggingface.co/google/medgemma-27b-text-it) | Generates NHS clinic letters from transcript + EHR context |

Additionally, a QLoRA fine-tuned adapter is published at [`yashvshetty/clarke-medgemma-27b-lora`](https://huggingface.co/yashvshetty/clarke-medgemma-27b-lora) (173.4 MB, LoRA rank 16, trained on 5 NHS clinic letter examples).

---

## Evaluation Summary

Full methodology, per-patient results, error taxonomy, and limitations are documented in the [evaluation report](evaluation/EVALUATION.md). Headline findings:

**MedASR (Word Error Rate: 13.28%)** Most clinical terms transcribed correctly. Errors concentrated on patient names (resolved from EHR, not transcript) and rare medical terms. Downstream agents correct most transcription errors using authoritative EHR data.

**EHR Agent (100% recall, 98.6% precision)** Every allergy, medication, lab result, and diagnosis was retrieved across all five patients. One borderline hallucination occurred (a clinically correct trend annotation). The deterministic query architecture guarantees no stored fact is missed.

**Document Generation (BLEU-1 0.71 after QLoRA)** The base model scored BLEU-1 0.54. After QLoRA fine-tuning on 5 gold-standard NHS letters (15 minutes of training, single A100), BLEU-1 rose to 0.71 (+31%). All generated letters correctly captured diagnoses, medications, lab results, and management plans.

---

## QLoRA Fine-Tuning

Clarke includes a QLoRA fine-tuning pipeline for adapting MedGemma 27B to NHS letter conventions.

| Parameter | Value |
|-----------|-------|
| Method | QLoRA (4-bit base + LoRA rank 16, alpha 32) |
| Target modules | q_proj, k_proj, v_proj, o_proj |
| Training data | 5 gold-standard NHS clinic letters |
| Training time | ~15 minutes on A100 40 GB (Google Colab) |
| Framework | Unsloth |
| Adapter size | 173.4 MB |
| Result | BLEU-1 improved from 0.54 to 0.71 (+31%) |

Training scripts are in [`finetuning/`](finetuning/). The adapter is published at [`yashvshetty/clarke-medgemma-27b-lora`](https://huggingface.co/yashvshetty/clarke-medgemma-27b-lora).

---

## Quick Start

### Run in mock mode (no GPU required)

```bash
git clone https://github.com/yvs-tinker/clarke.git
cd clarke
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

USE_MOCK_FHIR=true MEDASR_MODEL_ID=mock MEDGEMMA_4B_MODEL_ID=mock MEDGEMMA_27B_MODEL_ID=mock python3 app.py
```

Open [http://localhost:7860](http://localhost:7860).

### Run with real models (requires A100 GPU + HuggingFace access)

Create a `.env` file:

```
MEDASR_MODEL_ID=google/medasr
MEDGEMMA_4B_MODEL_ID=google/medgemma-1.5-4b-it
MEDGEMMA_27B_MODEL_ID=google/medgemma-27b-text-it
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
FHIR_BASE_URL=http://localhost:8080/fhir
APP_HOST=0.0.0.0
APP_PORT=7860
```

Then launch with `python3 app.py`. Requires NVIDIA A100 80 GB for the full three-model pipeline.

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
│   │   └── mock_api.py       # Mock FHIR server for development
│   └── prompts/              # Jinja2 prompt templates
├── frontend/
│   ├── ui.py                 # Gradio interface builder
│   ├── components.py         # UI screen components
│   ├── state.py              # Session state management
│   └── assets/               # CSS, logo, static files
├── data/                     # Demo audio, transcripts, synthetic FHIR bundles
├── evaluation/               # Evaluation scripts and report
│   ├── EVALUATION.md         # Full evaluation report
│   ├── eval_medasr.py        # Word Error Rate evaluation
│   ├── eval_ehr_agent.py     # EHR fact recall evaluation
│   ├── eval_doc_gen.py       # BLEU/ROUGE-L evaluation
│   └── gold_standards/       # Reference letters for scoring
├── finetuning/               # LoRA training scripts and adapter
└── tests/                    # Unit, integration, and end-to-end tests
```

---

## Development

Clarke was built by a solo 4th-year medical student over the competition period. Development used Claude (Anthropic) for architectural design, evaluation methodology, and technical problem-solving, and Codex (GitHub) for code implementation via pull requests.

Key technical decisions documented in the [evaluation report](evaluation/EVALUATION.md):
- **Deterministic EHR retrieval over agentic tool-calling** after prototyping showed MedGemma 4B's agentic queries were unreliable.
- **Full bfloat16 precision for inference** after discovering 4-bit quantisation breaks weight tying in MedGemma 27B.
- **Multi-agent error correction** where each pipeline stage compensates for upstream errors.

---

## Licence

- **Code:** [Apache 2.0](LICENSE)
- **Models:** Subject to [HAI-DEF Terms of Use](https://developers.google.com/health-ai-developer-foundations/terms) and HuggingFace gating requirements.

---

## Acknowledgements

- [MedGemma Impact Challenge](https://www.kaggle.com/competitions/medgemma-impact-challenge) by Google Health AI
- [HAI-DEF](https://goo.gle/hai-def) model releases
- [Synthea](https://synthetichealth.github.io/synthea/) for synthetic patient data
- [HAPI FHIR](https://hapifhir.io/) server ecosystem
