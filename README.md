---
title: Clarke
emoji: 🩺
colorFrom: blue
colorTo: gold
sdk: docker
app_port: 7860
hardware: a100-large
---

# Clarke

Clarke is an AI-assisted ambient clinical documentation pipeline for NHS outpatient consultations, combining speech transcription, EHR context retrieval, and structured letter generation.

## Architecture (3-model pipeline)

```text
Audio (upload / record)
        |
        v
+---------------------------+
| MedASR (google/medasr)    |
| Consultation transcript   |
+---------------------------+
        |
        +------------------------------+
        |                              |
        v                              v
+---------------------------+   +---------------------------+
| EHR Agent                 |   | Mock/Live FHIR API        |
| MedGemma 4B IT            |<->| Patient records           |
| Context synthesis (JSON)  |   | (conditions, meds, labs)  |
+---------------------------+   +---------------------------+
        |
        v
+---------------------------+
| Document Generator        |
| MedGemma 27B Text-IT      |
| NHS clinic letter output  |
+---------------------------+
        |
        v
Clinician review, edits, sign-off
```

## Features

- End-to-end ambient documentation workflow across 6 UI screens.
- FHIR-backed context enrichment with patient demographics, conditions, medications, labs, allergies, and reports.
- Deterministic fallback paths for reliability when model/tool behavior degrades.
- Demo-ready synthetic patient dataset and consultation audio/transcripts.
- Evaluation scripts for WER (ASR), fact recall (EHR extraction), and BLEU/ROUGE-L (letter generation).
- Mock-safe local mode (`USE_MOCK_MODELS=true`, `USE_MOCK_FHIR=true`) for reproducible development without gated model access.

## Quick Start

### 1) Clone and install

```bash
git clone <your-github-repo-url>.git
cd clarke
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env` in project root:

```bash
MEDASR_MODEL_ID=google/medasr
MEDGEMMA_4B_MODEL_ID=google/medgemma-1.5-4b-it
MEDGEMMA_27B_MODEL_ID=google/medgemma-27b-text-it
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx

USE_MOCK_FHIR=true
USE_MOCK_MODELS=true

FHIR_BASE_URL=http://localhost:8080/fhir
APP_HOST=0.0.0.0
APP_PORT=7860
```

### 3) Run local services

```bash
python -m backend.fhir.mock_api
```

Open a second terminal:

```bash
python app.py
```

Then browse to `http://localhost:7860`.

## Evaluation Results

Latest summary from `evaluation_report.md`:

- **MedASR WER (mock):** 0.0000 average across 3 demo clips.
- **EHR Fact Recall:** recall 1.0000, precision 0.9867, hallucination 0.0133 (all targets passed).
- **Document generation (mock):** BLEU 0.5668, ROUGE-L 0.0977.

## Models (HAI-DEF)

- **MedASR (transcription):** [`google/medasr`](https://huggingface.co/google/medasr)
- **MedGemma 1.5 4B IT (EHR agent):** [`google/medgemma-1.5-4b-it`](https://huggingface.co/google/medgemma-1.5-4b-it)
- **MedGemma 27B Text-IT (document generation):** [`google/medgemma-27b-text-it`](https://huggingface.co/google/medgemma-27b-text-it)

## Links

- **HF Space demo:** add your public Space URL here (Task 34 output).
- **HF LoRA adapter:** skipped in this run because no publishable adapter artifact was available (`finetuning/adapter/task35_publication_status.md`).

## Repository Structure

- `backend/` — orchestration, model wrappers, FHIR client/API, prompts, schemas.
- `frontend/` — Gradio UI screens, styling, and event bindings.
- `data/` — demo audio/transcripts and synthetic FHIR bundles.
- `evaluation/` — reproducible evaluation scripts and metric outputs.
- `tests/` — unit/integration/e2e validation.

## Licence

- **Code:** Apache 2.0 (`LICENSE`).
- **Models:** subject to HAI-DEF model terms and Hugging Face gating/licensing requirements.

## Acknowledgements

- MedGemma Impact Challenge
- Google HAI-DEF model releases
- Synthea synthetic patient generation project
- HAPI FHIR ecosystem and FHIR standard tooling
