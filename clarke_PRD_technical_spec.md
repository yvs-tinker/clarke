# Clarke — PRD Technical Specification

**Version:** 1.0 | **Date:** 13 February 2026 | **Author:** Project Lead  
**Status:** Final — engineering blueprint for AI agent (Codex) execution  
**Parent document:** clarke_PRD_masterplan.md  
**Scope:** Architecture, directory structure, technology stack, data models, API contracts, model serving, FHIR specification, synthetic data, frontend–backend integration, error handling, testing, and known pitfalls  
**Not in scope:** Strategic rationale (masterplan.md), build sequencing (implementation.md), visual styling (design_guidelines.md), user journey (userflow.md), granular task list (tasks.md)

---

## 1. Project Directory Tree

```
clarke/
├── app.py                          # Gradio application entry point (launches UI + mounts FastAPI)
├── Dockerfile                      # HF Spaces Docker config (nvidia/cuda:12.4.1-runtime-ubuntu22.04)
├── requirements.txt                # Pinned Python dependencies
├── .env.template                   # Environment variable template (copy to .env)
├── README.md                       # Project overview, architecture diagram, setup, evaluation, licence
├── LICENSE                         # Apache 2.0
├── submission_checklist.md         # Competition submission verification checklist
├── evaluation_report.md            # Quantitative evaluation results (WER, BLEU, ROUGE-L, fact recall)
│
├── backend/
│   ├── __init__.py
│   ├── orchestrator.py             # Core pipeline coordinator: audio → transcript → context → letter
│   ├── api.py                      # FastAPI endpoints (patient, consultation, document, health)
│   ├── config.py                   # Centralised configuration (env vars, model IDs, timeouts)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── medasr.py               # MedASR loading, audio preprocessing, transcription pipeline
│   │   ├── ehr_agent.py            # MedGemma 4B EHR agent: FHIR tool-calling or deterministic fallback
│   │   ├── doc_generator.py        # MedGemma 27B document generation: prompt assembly + inference
│   │   └── model_manager.py        # Shared GPU memory management, model lifecycle, health checks
│   ├── fhir/
│   │   ├── __init__.py
│   │   ├── client.py               # Async FHIR REST client (httpx) for querying HAPI FHIR / mock API
│   │   ├── tools.py                # FHIR tool functions for EHR agent (search_patients, get_conditions, etc.)
│   │   ├── mock_api.py             # Mock FHIR API (FastAPI endpoints returning pre-loaded JSON) — fallback
│   │   └── queries.py              # Deterministic FHIR query patterns (fallback for agentic tool-calling)
│   ├── prompts/
│   │   ├── document_generation.j2  # Jinja2 template: system + transcript + context → letter prompt
│   │   ├── ehr_agent_system.txt    # System prompt for MedGemma 4B EHR agent
│   │   └── context_synthesis.j2    # Jinja2 template: raw FHIR resources → structured context JSON
│   ├── schemas.py                  # Pydantic data models (Patient, Consultation, Transcript, etc.)
│   ├── audio.py                    # Audio format conversion (WebM → WAV 16kHz mono via ffmpeg/pydub)
│   ├── errors.py                   # Custom exception classes, error response models, logging config
│   └── utils.py                    # Shared utilities (timing decorators, JSON sanitisation)
│
├── frontend/
│   ├── __init__.py
│   ├── ui.py                       # Gradio Blocks UI definition (all screens S1–S6)
│   ├── theme.py                    # Gradio theme: Clarke colour tokens, typography, spacing
│   ├── components.py               # Reusable Gradio component builders (patient card, status badge, etc.)
│   ├── state.py                    # Gradio session state management
│   └── assets/
│       ├── style.css               # Custom CSS (design_guidelines.md §1–§5 tokens and animations)
│       ├── clarke_logo.svg         # Clarke shield/C logo in SVG
│       └── favicon.ico             # Browser tab icon
│
├── data/
│   ├── synthea/
│   │   ├── generate.sh             # Synthea generation script (50 UK-style patients)
│   │   └── uk_config/              # Synthea UK module config (names, NHS numbers, mmol/L, BNF drugs)
│   ├── fhir_bundles/
│   │   └── *.json                  # Pre-generated FHIR Bundle JSON files (50 patients) for mock API
│   ├── demo/
│   │   ├── mrs_thompson.wav        # Demo audio: 67F, T2DM, rising HbA1c (~60s, 16kHz mono WAV)
│   │   ├── mr_okafor.wav           # Demo audio: chest pain follow-up (~60s, 16kHz mono WAV)
│   │   ├── ms_patel.wav            # Demo audio: asthma review (~60s, 16kHz mono WAV)
│   │   ├── mrs_thompson_transcript.txt  # Ground-truth transcript for WER evaluation
│   │   ├── mr_okafor_transcript.txt
│   │   └── ms_patel_transcript.txt
│   ├── training/
│   │   ├── train.jsonl             # 200 training triplets (transcript, context, reference letter)
│   │   └── test.jsonl              # 50 held-out test triplets
│   └── clinic_list.json            # Demo clinic list metadata (5 patients for dashboard)
│
├── finetuning/
│   ├── train_lora.py               # QLoRA fine-tuning script for MedGemma 27B
│   ├── generate_training_data.py   # Script to generate training triplets via Claude API
│   └── merge_adapter.py            # Merge LoRA adapter with base model (optional, for evaluation)
│
├── evaluation/
│   ├── eval_medasr.py              # WER evaluation: MedASR vs Whisper on test clips
│   ├── eval_ehr_agent.py           # Fact recall / precision / hallucination evaluation
│   ├── eval_doc_gen.py             # BLEU / ROUGE-L evaluation on held-out test set
│   └── gold_standards/
│       └── *.json                  # Gold-standard context summaries for 20 test patients
│
├── tests/
│   ├── test_api.py                 # API endpoint unit tests (one per endpoint)
│   ├── test_medasr.py              # MedASR pipeline unit tests
│   ├── test_ehr_agent.py           # EHR agent unit tests
│   ├── test_doc_generator.py       # Document generator unit tests
│   ├── test_fhir_client.py         # FHIR client unit tests
│   ├── test_schemas.py             # Pydantic model validation tests
│   └── test_e2e.py                 # End-to-end pipeline test (audio → transcript → context → letter)
│
└── scripts/
    ├── start.sh                    # Single-command launch script (starts FHIR + FastAPI + Gradio)
    ├── health_check.sh             # Verify all services running
    └── setup_fhir.sh               # Load synthetic data into FHIR server
```

---

## 2. Technology Stack

| Package | Version | Purpose | Notes |
|---|---|---|---|
| Python | 3.11.x | Runtime | HF Spaces base |
| PyTorch | 2.4.x | ML framework | CUDA 12.4 build |
| transformers | 4.47.x | Model loading (MedASR, MedGemma) | HuggingFace |
| bitsandbytes | 0.44.x | 4-bit NF4 quantisation | `pip install --break-system-packages` |
| accelerate | 1.2.x | Device mapping for multi-GPU/CPU offload | |
| peft | 0.13.x | LoRA / QLoRA fine-tuning | |
| trl | 0.12.x | SFTTrainer for supervised fine-tuning | |
| datasets | 3.2.x | HF Datasets for training data loading | |
| Gradio | 5.x | Frontend UI framework | Served within HF Space |
| FastAPI | 0.109.x | Backend REST API | Mounted within Gradio app |
| uvicorn | 0.27.x | ASGI server for FastAPI | |
| httpx | 0.27.x | Async HTTP client (FHIR REST calls) | |
| pydub | 0.25.x | Audio resampling, channel conversion | Requires ffmpeg |
| librosa | 0.10.x | Audio waveform loading / preprocessing | |
| ffmpeg | 7.x (system) | WebM → WAV format conversion | System package, not pip |
| jinja2 | 3.1.x | Prompt template engine | |
| jiwer | 3.0.x | WER computation for MedASR evaluation | |
| rouge_score | latest | ROUGE-L for document generation evaluation | |
| sacrebleu | latest | BLEU for document generation evaluation | |
| openai-whisper | large-v3 | ASR baseline comparison only | |
| reportlab | 4.2.x | PDF export of clinic letters | |
| wandb | 0.18.x | Experiment tracking (fine-tuning) | |
| huggingface_hub | latest | Model upload, Space deployment | |
| python-dotenv | latest | .env file loading | |
| loguru | latest | Structured logging | |

**Compute allocation:**

| Component | Runs On | Approx VRAM |
|---|---|---|
| MedASR (105M) | GPU | ~0.5 GB |
| MedGemma 4B (4-bit NF4) | GPU | ~3 GB |
| MedGemma 27B (4-bit NF4) | GPU | ~16 GB |
| FHIR server (HAPI or mock) | CPU | 0 (CPU/RAM only) |
| FastAPI / Gradio | CPU | 0 |
| **Total GPU** | | **~19.5 GB** (fits A100 40GB with headroom for KV cache + fine-tuning) |

---

## 3. Infrastructure and Environment Specification

### 3a. Environment Variables

```env
# .env.template — copy to .env and fill values

# === Model Configuration ===
MEDASR_MODEL_ID=google/medasr
MEDGEMMA_4B_MODEL_ID=google/medgemma-1.5-4b-it
MEDGEMMA_27B_MODEL_ID=google/medgemma-27b-text-it
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx           # HuggingFace token (gated model access)
QUANTIZE_4BIT=true                          # Enable 4-bit NF4 quantisation for 4B and 27B
USE_FLASH_ATTENTION=true                    # Enable flash attention if supported

# === FHIR Configuration ===
FHIR_SERVER_URL=http://localhost:8080/fhir  # HAPI FHIR or mock API base URL
USE_MOCK_FHIR=false                         # Set true to use mock FHIR API (fallback)
FHIR_TIMEOUT_S=10                           # FHIR query timeout in seconds

# === Application Configuration ===
APP_HOST=0.0.0.0
APP_PORT=7860                               # Gradio default port on HF Spaces
LOG_LEVEL=INFO                              # DEBUG | INFO | WARNING | ERROR
MAX_AUDIO_DURATION_S=1800                   # Maximum recording length (30 min)
PIPELINE_TIMEOUT_S=120                      # Max time for full pipeline (End Consultation → letter)
DOC_GEN_MAX_TOKENS=2048                     # Max tokens for MedGemma 27B generation
DOC_GEN_TEMPERATURE=0.3                     # Low temperature for factual clinical text

# === Fine-tuning (optional, Phase 4) ===
WANDB_API_KEY=                              # Weights & Biases API key
WANDB_PROJECT=clarke-finetuning
LORA_RANK=16
LORA_ALPHA=32
LORA_DROPOUT=0.05
TRAINING_EPOCHS=3
LEARNING_RATE=2e-4
BATCH_SIZE=2
GRAD_ACCUM_STEPS=8
MAX_SEQ_LENGTH=4096
```

### 3b. Cloud Deployment (Primary — HF Spaces A100)

**Dockerfile:**

```dockerfile
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    ffmpeg curl wget git && \
    rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.11 /usr/bin/python

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .

# Load FHIR data and start application
RUN chmod +x scripts/start.sh
EXPOSE 7860
CMD ["scripts/start.sh"]
```

**scripts/start.sh:**

```bash
#!/bin/bash
set -e

echo "=== Clarke Startup ==="

# 1. Start mock FHIR API (or HAPI FHIR) in background
if [ "$USE_MOCK_FHIR" = "true" ]; then
    echo "[1/3] Starting mock FHIR API..."
    python -m backend.fhir.mock_api &
    FHIR_PID=$!
    sleep 2
    echo "[1/3] Mock FHIR API running (PID: $FHIR_PID)"
else
    echo "[1/3] Using external FHIR server at $FHIR_SERVER_URL"
fi

# 2. Verify GPU
echo "[2/3] Checking GPU..."
python -c "import torch; assert torch.cuda.is_available(), 'No GPU'; print(f'GPU: {torch.cuda.get_device_name(0)}, VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB')"

# 3. Launch Gradio app (which mounts FastAPI)
echo "[3/3] Starting Clarke application on port ${APP_PORT:-7860}..."
python app.py

echo "=== Clarke is ready ==="
```

**HF Spaces metadata (in README.md YAML frontmatter):**

```yaml
---
title: Clarke
emoji: 🩺
colorFrom: blue
colorTo: gold
sdk: docker
app_port: 7860
hardware: a100-large
---
```

### 3c. Local Development (MacBook Pro M2 8GB — No GPU)

Local development runs **only** lightweight components. AI models are either mocked or served from a remote cloud GPU.

**Local setup:**

1. Clone repo. Copy `.env.template` to `.env`.
2. Set `USE_MOCK_FHIR=true` in `.env`.
3. Set model IDs to `mock` to activate stubs: `MEDASR_MODEL_ID=mock`, `MEDGEMMA_4B_MODEL_ID=mock`, `MEDGEMMA_27B_MODEL_ID=mock`.
4. `pip install -r requirements.txt` (CPU-only PyTorch).
5. `bash scripts/start.sh` → Gradio UI at `http://localhost:7860`.

**Model stubs (when model ID = "mock"):**

Each model module in `backend/models/` checks the model ID. If `mock`, it returns pre-loaded fixture data instead of running inference:

- **MedASR mock:** Returns the ground-truth transcript from `data/demo/*.txt` for known demo audio files, or a generic placeholder transcript for unknown audio.
- **MedGemma 4B mock:** Returns pre-built context JSON from `data/fhir_bundles/` for known patient IDs.
- **MedGemma 27B mock:** Returns a pre-written reference letter from `data/training/test.jsonl` for known patient IDs.

This allows full frontend + integration development without GPU access.

---

## 4. Data Models and Schemas

All models defined as Pydantic v2 `BaseModel` in `backend/schemas.py`.

```python
"""Clarke data models — Pydantic v2 schemas for all system objects."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


# === Enums ===

class ConsultationStatus(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    PROCESSING = "processing"
    REVIEW = "review"
    SIGNED_OFF = "signed_off"


class PipelineStage(str, Enum):
    TRANSCRIBING = "transcribing"
    RETRIEVING_CONTEXT = "retrieving_context"
    GENERATING_DOCUMENT = "generating_document"
    COMPLETE = "complete"
    FAILED = "failed"


# === Core Models ===

class Patient(BaseModel):
    """A patient in the clinic list."""
    id: str = Field(description="FHIR Patient resource ID")
    nhs_number: str = Field(description="NHS number (format: XXX XXX XXXX)")
    name: str = Field(description="Full name (e.g., 'Mrs. Margaret Thompson')")
    date_of_birth: str = Field(description="DOB in DD/MM/YYYY format")
    age: int
    sex: str = Field(description="'Male' or 'Female'")
    appointment_time: str = Field(description="HH:MM format")
    summary: str = Field(description="One-line clinical summary for dashboard card")


class LabResult(BaseModel):
    """A single laboratory result with trend."""
    name: str = Field(description="e.g., 'HbA1c'")
    value: str = Field(description="e.g., '55'")
    unit: str = Field(description="e.g., 'mmol/mol'")
    reference_range: Optional[str] = Field(default=None, description="e.g., '20-42'")
    date: str = Field(description="ISO date of result")
    trend: Optional[str] = Field(default=None, description="'rising', 'falling', 'stable', or None")
    previous_value: Optional[str] = Field(default=None, description="Previous result value")
    previous_date: Optional[str] = Field(default=None)
    fhir_resource_id: Optional[str] = Field(default=None, description="Source FHIR Observation ID")


class PatientContext(BaseModel):
    """Structured patient context synthesised by the EHR Agent from FHIR data."""
    patient_id: str
    demographics: dict = Field(description="name, dob, nhs_number, age, sex, address")
    problem_list: list[str] = Field(description="Active diagnoses, e.g., ['Type 2 Diabetes Mellitus (2019)', ...]")
    medications: list[dict] = Field(description="[{'name': 'Metformin', 'dose': '1g', 'frequency': 'BD', 'fhir_id': '...'}]")
    allergies: list[dict] = Field(description="[{'substance': 'Penicillin', 'reaction': 'Anaphylaxis', 'severity': 'high'}]")
    recent_labs: list[LabResult] = Field(default_factory=list)
    recent_imaging: list[dict] = Field(default_factory=list, description="[{'type': 'CXR', 'date': '...', 'summary': '...'}]")
    clinical_flags: list[str] = Field(default_factory=list, description="['HbA1c rising trend over 6 months']")
    last_letter_excerpt: Optional[str] = Field(default=None, description="Key excerpt from most recent clinic letter")
    retrieval_warnings: list[str] = Field(default_factory=list, description="Warnings if some FHIR queries failed")
    retrieved_at: str = Field(description="ISO timestamp of retrieval")


class Transcript(BaseModel):
    """Consultation transcript produced by MedASR."""
    consultation_id: str
    text: str = Field(description="Full transcript text")
    duration_s: float = Field(description="Audio duration in seconds")
    word_count: int
    created_at: str


class DocumentSection(BaseModel):
    """A single section of the generated clinical letter."""
    heading: str = Field(description="e.g., 'History of presenting complaint'")
    content: str = Field(description="Section body text")
    editable: bool = Field(default=True)
    fhir_sources: list[str] = Field(default_factory=list, description="FHIR resource IDs cited in this section")


class ClinicalDocument(BaseModel):
    """A generated NHS clinical letter."""
    consultation_id: str
    letter_date: str
    patient_name: str
    patient_dob: str
    nhs_number: str
    addressee: str = Field(description="GP name and address")
    salutation: str = Field(description="e.g., 'Dear Dr. Patel,'")
    sections: list[DocumentSection]
    medications_list: list[str] = Field(description="Current medications (formatted)")
    sign_off: str = Field(description="e.g., 'Dr. S. Chen, Consultant Diabetologist'")
    status: ConsultationStatus = ConsultationStatus.REVIEW
    generated_at: str
    generation_time_s: float = Field(description="Time taken for MedGemma 27B inference")
    discrepancies: list[dict] = Field(default_factory=list, description="[{'type': 'allergy_mismatch', 'detail': '...'}]")


class Consultation(BaseModel):
    """A complete consultation session — links patient, transcript, context, and document."""
    id: str = Field(description="Unique consultation ID (UUID)")
    patient: Patient
    status: ConsultationStatus = ConsultationStatus.IDLE
    pipeline_stage: Optional[PipelineStage] = None
    context: Optional[PatientContext] = None
    transcript: Optional[Transcript] = None
    document: Optional[ClinicalDocument] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    audio_file_path: Optional[str] = None


class PipelineProgress(BaseModel):
    """Real-time pipeline progress updates pushed to the UI."""
    consultation_id: str
    stage: PipelineStage
    progress_pct: int = Field(ge=0, le=100)
    message: str = Field(description="Human-readable status, e.g., 'Finalising transcript...'")


class ErrorResponse(BaseModel):
    """Standardised error response format."""
    error: str = Field(description="Error category: 'model_error', 'fhir_error', 'audio_error', 'timeout'")
    message: str = Field(description="Human-readable error message for UI display")
    detail: Optional[str] = Field(default=None, description="Technical detail (logged, not shown to user)")
    consultation_id: Optional[str] = None
    timestamp: str
```

**Relationships:**

- A `Consultation` belongs to one `Patient` and has at most one `Transcript`, one `PatientContext`, and one `ClinicalDocument`.
- A `PatientContext` contains lists of `LabResult` objects.
- A `ClinicalDocument` contains a list of `DocumentSection` objects.
- `PipelineProgress` is a transient event emitted during processing — not persisted.

---

## 5. API Contracts

All endpoints are served by FastAPI, mounted within the Gradio app at `/api/v1/`.

### 5a. Endpoint Summary

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | System health check (all models + FHIR) |
| GET | `/api/v1/patients` | List all patients in clinic list |
| GET | `/api/v1/patients/{patient_id}` | Get single patient details |
| POST | `/api/v1/patients/{patient_id}/context` | Trigger EHR Agent context retrieval |
| POST | `/api/v1/consultations/start` | Start a consultation (begin recording session) |
| POST | `/api/v1/consultations/{id}/audio` | Upload audio chunk or complete audio file |
| POST | `/api/v1/consultations/{id}/end` | End consultation → trigger full pipeline |
| GET | `/api/v1/consultations/{id}/transcript` | Get current transcript |
| GET | `/api/v1/consultations/{id}/document` | Get generated document |
| POST | `/api/v1/consultations/{id}/document/regenerate-section` | Regenerate one section |
| POST | `/api/v1/consultations/{id}/document/sign-off` | Sign off document |
| GET | `/api/v1/consultations/{id}/progress` | Get current pipeline progress |

### 5b. Endpoint Details

**GET `/api/v1/health`**

```json
// Response 200
{
  "status": "healthy",
  "models": {
    "medasr": {"loaded": true, "device": "cuda:0"},
    "medgemma_4b": {"loaded": true, "device": "cuda:0", "quantised": "4bit"},
    "medgemma_27b": {"loaded": true, "device": "cuda:0", "quantised": "4bit"}
  },
  "fhir": {"status": "connected", "patient_count": 50},
  "gpu": {"name": "A100-SXM4-40GB", "vram_used_gb": 19.5, "vram_total_gb": 40.0},
  "timestamp": "2026-02-13T14:00:00Z"
}
```

**GET `/api/v1/patients`**

```json
// Response 200
{
  "patients": [
    {
      "id": "pt-001",
      "nhs_number": "943 476 5829",
      "name": "Mrs. Margaret Thompson",
      "date_of_birth": "14/03/1958",
      "age": 67,
      "sex": "Female",
      "appointment_time": "14:00",
      "summary": "Follow-up — Type 2 Diabetes, rising HbA1c"
    }
  ]
}
```

**POST `/api/v1/patients/{patient_id}/context`**

```json
// Request: empty body (patient_id in URL path)
// Response 200: PatientContext JSON (see §4 schema)
// Response 404: {"error": "fhir_error", "message": "Patient not found in EHR", ...}
// Response 504: {"error": "timeout", "message": "EHR context retrieval timed out", ...}
```

**POST `/api/v1/consultations/start`**

```json
// Request
{"patient_id": "pt-001"}

// Response 201
{
  "consultation_id": "cons-uuid-xxxx",
  "patient_id": "pt-001",
  "status": "recording",
  "started_at": "2026-02-13T14:05:00Z"
}
```

**POST `/api/v1/consultations/{id}/audio`**

```json
// Request: multipart/form-data
// Field: "audio_file" — WAV file (16kHz mono) or WebM (server converts)
// Field: "is_final" — boolean (true = complete audio, false = chunk for streaming)

// Response 200
{"consultation_id": "cons-uuid-xxxx", "audio_received": true, "duration_s": 62.5}
```

**POST `/api/v1/consultations/{id}/end`**

This is the main pipeline trigger. It finalises the transcript, synthesises context, and generates the document.

```json
// Request: empty body (or optionally upload final audio)
// Response 202 (Accepted — processing started)
{
  "consultation_id": "cons-uuid-xxxx",
  "status": "processing",
  "pipeline_stage": "transcribing",
  "message": "Pipeline started. Poll /progress for updates."
}

// Error 408: {"error": "timeout", "message": "Pipeline exceeded 120s timeout", ...}
// Error 500: {"error": "model_error", "message": "Document generation failed", ...}
```

**GET `/api/v1/consultations/{id}/document`**

```json
// Response 200: ClinicalDocument JSON (see §4 schema)
// Response 404: {"error": "not_found", "message": "No document generated yet"}
```

**POST `/api/v1/consultations/{id}/document/regenerate-section`**

```json
// Request
{"section_index": 2, "instruction": "Make this section more concise"}

// Response 200
{"section_index": 2, "heading": "Investigation results", "content": "...(regenerated)..."}
```

**POST `/api/v1/consultations/{id}/document/sign-off`**

```json
// Request
{"edited_sections": [{"index": 1, "content": "Updated text..."}]}

// Response 200
{"consultation_id": "...", "status": "signed_off", "signed_at": "2026-02-13T14:08:00Z"}
```

**GET `/api/v1/consultations/{id}/progress`**

```json
// Response 200: PipelineProgress JSON
{
  "consultation_id": "...",
  "stage": "generating_document",
  "progress_pct": 66,
  "message": "Generating clinical letter..."
}
```

---

## 6. Model Serving Specification

### 6a. MedASR (Speech Recognition)

| Property | Value |
|---|---|
| **HF Model ID** | `google/medasr` |
| **Parameters** | 105M |
| **Architecture** | Conformer-based ASR (AutoModelForSpeechSeq2Seq) |
| **GPU VRAM** | ~0.5 GB |
| **Quantisation** | None needed (small model) |
| **Loading** | `transformers.pipeline("automatic-speech-recognition", model="google/medasr", device="cuda:0")` |

**Input format:**

```python
# 16kHz mono WAV, float32 waveform
# Loaded via librosa or pydub
import librosa
waveform, sr = librosa.load("audio.wav", sr=16000, mono=True)
# waveform: numpy array, shape (n_samples,), dtype float32
```

**Inference call:**

```python
result = pipeline(
    waveform,
    chunk_length_s=20,
    stride_length_s=(4, 2),
    return_timestamps=True,
    generate_kwargs={"language": "en", "task": "transcribe"}
)
transcript_text = result["text"]
```

**Output format:**

```json
{
  "text": "Hello Mrs Thompson, good to see you again. How have you been since we last met?",
  "chunks": [
    {"text": "Hello Mrs Thompson,", "timestamp": [0.0, 1.5]},
    {"text": "good to see you again.", "timestamp": [1.5, 3.2]}
  ]
}
```

**Timeout:** 30s per 60s of audio. **Retry:** 1 retry on timeout.

**Mock (local dev):** Return text from `data/demo/{patient}_transcript.txt`.

### 6b. MedGemma 1.5 4B (EHR Agent)

| Property | Value |
|---|---|
| **HF Model ID** | `google/medgemma-1.5-4b-it` |
| **Parameters** | 4B |
| **Architecture** | Gemma-based, instruction-tuned, multimodal (text capabilities used) |
| **GPU VRAM** | ~3 GB (4-bit NF4) |
| **Quantisation** | 4-bit NF4 via bitsandbytes (`load_in_4bit=True`, `bnb_4bit_compute_dtype=bfloat16`) |

**Loading:**

```python
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained("google/medgemma-1.5-4b-it")
model = AutoModelForCausalLM.from_pretrained(
    "google/medgemma-1.5-4b-it",
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
```

**Primary mode — Agentic tool-calling via LangGraph:**

The EHR Agent receives a patient ID, plans which FHIR queries to run, executes them, and synthesises a structured PatientContext JSON. If LangGraph tool-calling works reliably, this is the preferred mode.

**Fallback mode — Deterministic FHIR + MedGemma summarisation:**

If MedGemma 4B's instruction-following is unreliable (see §12), use deterministic Python functions to execute a fixed set of FHIR queries, then pass the raw FHIR JSON to MedGemma 4B for summarisation into the PatientContext schema only.

**FHIR tool functions available to the agent:**

```python
def search_patients(name: str) -> list[dict]:    # GET /fhir/Patient?name={name}
def get_conditions(patient_id: str) -> list[dict]:  # GET /fhir/Condition?patient={id}
def get_medications(patient_id: str) -> list[dict]: # GET /fhir/MedicationRequest?patient={id}
def get_observations(patient_id: str, category: str = "laboratory") -> list[dict]:
    # GET /fhir/Observation?patient={id}&category={category}&_sort=-date&_count=20
def get_allergies(patient_id: str) -> list[dict]:   # GET /fhir/AllergyIntolerance?patient={id}
def get_diagnostic_reports(patient_id: str) -> list[dict]:
    # GET /fhir/DiagnosticReport?patient={id}&_sort=-date&_count=5
def get_recent_encounters(patient_id: str) -> list[dict]:
    # GET /fhir/Encounter?patient={id}&_sort=-date&_count=3
```

**System prompt (ehr_agent_system.txt):**

```
You are a clinical EHR navigation agent. Your task is to retrieve and synthesise a patient's medical context from FHIR resources to support clinical documentation.

Given a patient ID, use the available FHIR tools to retrieve:
1. Demographics (Patient resource)
2. Active conditions/diagnoses (Condition resources)
3. Current medications (MedicationRequest resources)
4. Allergies (AllergyIntolerance resources)
5. Recent laboratory results — last 6 months (Observation resources, category=laboratory)
6. Recent imaging reports (DiagnosticReport resources)

After retrieval, synthesise the data into the following JSON structure ONLY. Do not include any explanation, commentary, or markdown formatting. Output ONLY valid JSON:

{
  "patient_id": "...",
  "demographics": {...},
  "problem_list": ["..."],
  "medications": [{...}],
  "allergies": [{...}],
  "recent_labs": [{...}],
  "recent_imaging": [{...}],
  "clinical_flags": ["..."],
  "last_letter_excerpt": "...",
  "retrieval_warnings": [],
  "retrieved_at": "..."
}
```

**Output parsing (critical — see §12):**

```python
import re, json

def parse_agent_output(raw_output: str) -> dict:
    """Extract JSON from MedGemma 4B output, stripping meta-commentary."""
    # Remove system prompt leaks
    raw_output = re.sub(r'<\|system\|>.*?<\|end\|>', '', raw_output, flags=re.DOTALL)
    # Remove markdown code fences
    raw_output = re.sub(r'```json\s*', '', raw_output)
    raw_output = re.sub(r'```\s*', '', raw_output)
    # Extract first JSON object
    match = re.search(r'\{[\s\S]*\}', raw_output)
    if match:
        return json.loads(match.group())
    raise ValueError("No valid JSON found in agent output")
```

**Timeout:** 15s for context retrieval. **Retry:** 1 retry. **Fallback on failure:** Return partial context with `retrieval_warnings`.

### 6c. MedGemma 27B (Document Generation)

| Property | Value |
|---|---|
| **HF Model ID** | `google/medgemma-27b-text-it` |
| **Parameters** | 27B |
| **Architecture** | Gemma-based, text-only, instruction-tuned |
| **GPU VRAM** | ~16 GB (4-bit NF4) |
| **Quantisation** | 4-bit NF4 via bitsandbytes (same config as 4B but for 27B model) |

**Loading:**

```python
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained("google/medgemma-27b-text-it")
model = AutoModelForCausalLM.from_pretrained(
    "google/medgemma-27b-text-it",
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
```

**Prompt template (document_generation.j2):**

```jinja2
<|system|>
You are an NHS clinical documentation assistant. Generate a structured NHS clinic letter from the consultation transcript and patient context provided below.

FORMAT REQUIREMENTS:
- Date: {{ letter_date }}
- Addressee: GP (name and address from patient record)
- Re: Patient name, DOB
- Salutation: "Dear Dr. [GP name],"
- Sections: History of presenting complaint | Examination findings (if discussed) | Investigation results (use EXACT values from patient context) | Assessment and plan | Current medications
- Sign-off: "Yours sincerely, {{ clinician_name }}, {{ clinician_title }}"

RULES:
1. Use EXACT lab values from the patient context — do not fabricate or round values.
2. Include both positive and negative findings discussed in the consultation.
3. If the transcript mentions a result, cross-reference it with the patient context. If values differ, flag with [DISCREPANCY].
4. Write in third person, past tense, formal British medical English.
5. Do NOT include information not discussed in the consultation or present in the patient context.
6. Keep the letter concise — aim for 300-500 words.
<|end|>

<|user|>
## CONSULTATION TRANSCRIPT
{{ transcript }}

## PATIENT CONTEXT (from Electronic Health Record)
{{ context_json }}

Generate the NHS clinic letter now.
<|end|>

<|assistant|>
```

**Generation parameters:**

```python
generation_config = {
    "max_new_tokens": 2048,
    "temperature": 0.3,
    "top_p": 0.9,
    "top_k": 40,
    "do_sample": True,
    "repetition_penalty": 1.1,
}
```

**Output parsing:** Split generated text into sections by detecting headings (bold markers or known section names). Return as list of `DocumentSection` objects.

**Timeout:** 90s. **Retry:** 1 retry with reduced `max_new_tokens=1024`. **Fallback on total failure:** Use MedGemma 4B with extensive prompt engineering for generation (lower quality but functional).

**Fallback loading if 27B fails on A100 40GB:**
1. Try GGUF Q8_0 via Ollama (`ollama run hf.co/unsloth/medgemma-27b-it-GGUF:Q8_0`). Switch inference to Ollama REST API (`POST http://localhost:11434/api/generate`).
2. If Ollama fails: use MedGemma 4B for generation.

---

## 7. FHIR Server Specification

### 7a. Primary: HAPI FHIR Server

- **Image:** `hapiproject/hapi:v7.4.0`
- **FHIR Version:** R4
- **Port:** 8080 (internal)
- **Data:** 50 Synthea-generated UK-style patients loaded via `POST /fhir` Bundle transactions.

### 7b. FHIR Resources Used

| Resource Type | Purpose | Key Fields |
|---|---|---|
| Patient | Demographics | name, birthDate, identifier (NHS number), gender, address |
| Condition | Problem list / diagnoses | code (SNOMED), clinicalStatus, onsetDateTime |
| MedicationRequest | Current medications | medicationCodeableConcept, dosageInstruction, status=active |
| Observation | Lab results | code (LOINC), valueQuantity, effectiveDateTime, referenceRange |
| AllergyIntolerance | Allergies | code, reaction, criticality |
| DiagnosticReport | Imaging / reports | code, conclusion, effectiveDateTime |
| Encounter | Recent visits | type, period, reasonCode |

### 7c. FHIR Query Patterns

```
GET /fhir/Patient/{id}
GET /fhir/Patient?name={name}&_count=10
GET /fhir/Condition?patient={id}&clinical-status=active
GET /fhir/MedicationRequest?patient={id}&status=active
GET /fhir/Observation?patient={id}&category=laboratory&_sort=-date&_count=20
GET /fhir/AllergyIntolerance?patient={id}
GET /fhir/DiagnosticReport?patient={id}&_sort=-date&_count=5
GET /fhir/Encounter?patient={id}&_sort=-date&_count=3
```

### 7d. Fallback: Mock FHIR API

If HAPI FHIR setup fails within HF Spaces Docker (Risk 5 in masterplan.md §8), replace with `backend/fhir/mock_api.py` — a FastAPI app that serves pre-loaded JSON from `data/fhir_bundles/`. Exposes the same REST endpoints. The EHR Agent code makes identical HTTP calls either way.

```python
# mock_api.py — simplified structure
from fastapi import FastAPI
import json, os

app = FastAPI()
BUNDLES_DIR = "data/fhir_bundles"

@app.get("/fhir/Patient/{patient_id}")
async def get_patient(patient_id: str):
    return load_resource(patient_id, "Patient")

@app.get("/fhir/Condition")
async def get_conditions(patient: str):
    return load_resources(patient, "Condition")

# ... same pattern for all resource types
```

---

## 8. Synthetic Data Specification

### 8a. Patients

**50 Synthea-generated patients** with UK customisation:

- **Names:** UK-style (e.g., Margaret Thompson, Emeka Okafor, Priya Patel). Manually patched for 5 demo patients.
- **Identifiers:** NHS numbers (format: XXX XXX XXXX, 10 digits, valid checksum).
- **Units:** mmol/L for glucose, mmol/mol for HbA1c, μmol/L for creatinine, mL/min for eGFR.
- **Drug names:** BNF-standard (metformin, ramipril, atorvastatin — not brand names).
- **Clinical scenarios:** Distributed across: diabetes (10), COPD (5), heart failure (5), CKD (5), hypertension (5), cancer follow-up (3), mental health (3), orthopaedic (3), asthma (5), miscellaneous (6).

### 8b. Demo Patients (3 primary + 2 supporting)

| # | Name | Age/Sex | Scenario | Key FHIR Data | Demo Audio |
|---|---|---|---|---|---|
| 1 | Mrs. Margaret Thompson | 67F | T2DM, rising HbA1c, start gliclazide | HbA1c 55↑ (was 48), eGFR 52↓, Penicillin allergy, Metformin 1g BD | ✅ ~60s WAV |
| 2 | Mr. Emeka Okafor | 54M | Chest pain follow-up post-angiography | Normal coronaries on angiogram, Troponin negative, BP 148/92 | ✅ ~60s WAV |
| 3 | Ms. Priya Patel | 28F | Asthma review, poor inhaler technique | Peak flow 320 (pred 450), Salbutamol 4x/week, no preventer | ✅ ~60s WAV |
| 4 | Mr. David Williams | 72M | Heart failure review | EF 35%, BNP 450, on bisoprolol + ramipril + furosemide | Dashboard only |
| 5 | Mrs. Fatima Khan | 45F | Depression follow-up | PHQ-9 score 12, on sertraline 100mg | Dashboard only |

### 8c. Example FHIR Patient Resource

```json
{
  "resourceType": "Patient",
  "id": "pt-001",
  "identifier": [
    {
      "system": "https://fhir.nhs.uk/Id/nhs-number",
      "value": "9434765829"
    }
  ],
  "name": [
    {
      "use": "official",
      "prefix": ["Mrs"],
      "given": ["Margaret"],
      "family": "Thompson"
    }
  ],
  "gender": "female",
  "birthDate": "1958-03-14",
  "address": [
    {
      "line": ["12 Oak Lane"],
      "city": "London",
      "postalCode": "SE1 4AB",
      "country": "GB"
    }
  ],
  "generalPractitioner": [
    {
      "display": "Dr. R. Patel, Riverside Medical Centre"
    }
  ]
}
```

### 8d. Example FHIR Observation (Lab Result)

```json
{
  "resourceType": "Observation",
  "id": "obs-hba1c-001",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "laboratory"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "4548-4",
        "display": "Hemoglobin A1c/Hemoglobin.total in Blood"
      }
    ],
    "text": "HbA1c"
  },
  "subject": {"reference": "Patient/pt-001"},
  "effectiveDateTime": "2026-01-15",
  "valueQuantity": {
    "value": 55,
    "unit": "mmol/mol",
    "system": "http://unitsofmeasure.org",
    "code": "mmol/mol"
  },
  "referenceRange": [
    {
      "low": {"value": 20, "unit": "mmol/mol"},
      "high": {"value": 42, "unit": "mmol/mol"},
      "text": "20-42 mmol/mol (normal)"
    }
  ]
}
```

### 8e. Example FHIR AllergyIntolerance

```json
{
  "resourceType": "AllergyIntolerance",
  "id": "allergy-001",
  "clinicalStatus": {
    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
  },
  "type": "allergy",
  "category": ["medication"],
  "criticality": "high",
  "code": {
    "coding": [{"system": "http://snomed.info/sct", "code": "764146007", "display": "Penicillin"}],
    "text": "Penicillin"
  },
  "patient": {"reference": "Patient/pt-001"},
  "reaction": [
    {
      "manifestation": [{"coding": [{"display": "Anaphylaxis"}]}],
      "severity": "severe"
    }
  ]
}
```

### 8f. Example FHIR Condition

```json
{
  "resourceType": "Condition",
  "id": "cond-t2dm-001",
  "clinicalStatus": {
    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
  },
  "code": {
    "coding": [{"system": "http://snomed.info/sct", "code": "44054006", "display": "Type 2 diabetes mellitus"}],
    "text": "Type 2 Diabetes Mellitus"
  },
  "subject": {"reference": "Patient/pt-001"},
  "onsetDateTime": "2019-06-01"
}
```

### 8g. Audio Files

- **Format:** WAV, 16kHz sample rate, mono, 16-bit PCM.
- **Duration:** 60–90 seconds each.
- **Content:** Simulated clinician–patient dialogue. Clear speech, minimal background noise. UK-accented English where possible.
- **Generation:** Self-recorded or generated via TTS (e.g., Google Cloud TTS with en-GB voices). Post-processed with `ffmpeg -i input.webm -ar 16000 -ac 1 -acodec pcm_s16le output.wav`.

### 8h. Demo Clinic List (clinic_list.json)

```json
{
  "clinician": {
    "name": "Dr. Sarah Chen",
    "specialty": "Diabetes & Endocrinology",
    "title": "Consultant Diabetologist"
  },
  "date": "13 February 2026",
  "patients": [
    {"id": "pt-001", "name": "Mrs. Margaret Thompson", "age": 67, "sex": "Female", "time": "14:00", "summary": "Follow-up — Type 2 Diabetes, rising HbA1c"},
    {"id": "pt-002", "name": "Mr. Emeka Okafor", "age": 54, "sex": "Male", "time": "14:20", "summary": "Follow-up — Chest pain, post-angiography"},
    {"id": "pt-003", "name": "Ms. Priya Patel", "age": 28, "sex": "Female", "time": "14:40", "summary": "Review — Asthma, poor symptom control"},
    {"id": "pt-004", "name": "Mr. David Williams", "age": 72, "sex": "Male", "time": "15:00", "summary": "Review — Heart failure, recent decompensation"},
    {"id": "pt-005", "name": "Mrs. Fatima Khan", "age": 45, "sex": "Female", "time": "15:20", "summary": "Follow-up — Depression, medication review"}
  ]
}
```

---

## 9. Frontend–Backend Integration

### 9a. Architecture Pattern

**Single Gradio app with embedded FastAPI.** The Gradio Blocks UI and the FastAPI backend run in the same Python process. Gradio handles the browser-facing UI and calls backend functions directly via Python (no HTTP for Gradio ↔ backend communication within the same process). The FastAPI routes are mounted for external access and for structured API contracts (testing, future clients).

```python
# app.py — simplified structure
import gradio as gr
from fastapi import FastAPI
from backend.api import router as api_router
from frontend.ui import build_ui

fast_api = FastAPI()
fast_api.include_router(api_router, prefix="/api/v1")

demo = build_ui()  # Returns gr.Blocks
demo = gr.mount_gradio_app(fast_api, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fast_api, host="0.0.0.0", port=7860)
```

### 9b. State Management

- **Session state:** Managed via `gr.State` — holds the current `Consultation` object (including patient, transcript, context, document, status).
- **No database.** All state is in-memory per session. State resets on page refresh (per userflow.md §5).
- **No localStorage.** No browser-side persistence.

### 9c. Screen ↔ Backend Mapping

| Screen | User Action | Gradio Event | Backend Call | UI Update |
|---|---|---|---|---|
| S1 (Dashboard) | Click patient card | `gr.Button.click` | `get_patient_context(patient_id)` → calls FHIR agent | Transition to S2, populate context panel |
| S2 (Patient Context) | Click "Start Consultation" | `gr.Button.click` | `start_consultation(patient_id)` | Transition to S3, start audio capture JS |
| S3 (Live Consultation) | Audio streaming | JavaScript `MediaRecorder` → WebSocket or periodic upload | `upload_audio_chunk()` | Live transcript panel updates |
| S3 | Click "End Consultation" | `gr.Button.click` | `end_consultation(consultation_id)` → triggers full pipeline | Transition to S4, show progress |
| S4 (Processing) | Automatic | Polling via `gr.Timer` or `gr.every()` | `get_pipeline_progress()` | Progress bar fills through 3 stages |
| S4 → S5 | Pipeline complete | Progress reaches 100% | `get_document()` | Transition to S5, reveal letter |
| S5 (Document Review) | Click paragraph to edit | JavaScript `contenteditable` | Edit stored in `gr.State` | Paragraph highlight, gold border |
| S5 | Click "Regenerate" on section | `gr.Button.click` | `regenerate_section(consultation_id, section_idx)` | Section skeleton → new text |
| S5 | Click "Sign Off" | `gr.Button.click` | `sign_off(consultation_id, edited_sections)` | Transition to S6, status → green |
| S6 (Signed Off) | Click "Next Patient" | `gr.Button.click` | Reset `gr.State` | Transition to S1 |

### 9d. Real-Time Updates

**Pipeline progress (S4):** Use `gr.Timer(every=1)` to poll `get_pipeline_progress()` every second during the processing state. When `stage == "complete"`, stop polling and transition to S5.

**Live transcript (S3):** Two options depending on Gradio capability:
1. **Preferred:** JavaScript interop — browser `MediaRecorder` captures audio chunks every 5s, sends via `fetch()` to `/api/v1/consultations/{id}/audio`, receives partial transcript in response. Update transcript `gr.Textbox` via Gradio event.
2. **Fallback:** No streaming transcript. Audio is captured entirely in browser, sent as one file when "End Consultation" is clicked. Transcript appears only during processing.

### 9e. Audio Capture

```javascript
// JavaScript injected into Gradio via gr.HTML or gr.JavaScript
// Captures audio from browser microphone, sends chunks to backend

const mediaRecorder = new MediaRecorder(stream, {mimeType: 'audio/webm;codecs=opus'});
mediaRecorder.ondataavailable = async (e) => {
    const formData = new FormData();
    formData.append('audio_file', e.data, 'chunk.webm');
    formData.append('is_final', 'false');
    await fetch(`/api/v1/consultations/${consultationId}/audio`, {
        method: 'POST', body: formData
    });
};
mediaRecorder.start(5000); // Chunk every 5 seconds
```

Server-side conversion in `backend/audio.py`:

```python
from pydub import AudioSegment

def convert_to_wav_16k(input_path: str, output_path: str) -> str:
    """Convert any audio format to 16kHz mono WAV for MedASR."""
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(output_path, format="wav")
    return output_path
```

---

## 10. Error Handling and Resilience

### 10a. Tiered Error Strategy

**Tier 1 — Self-healing (user never notices):**

| Failure | Retry Policy | Circuit Breaker |
|---|---|---|
| FHIR query timeout | 2 retries, backoff [1s, 3s] | After 3 consecutive failures, mark FHIR as degraded |
| MedASR chunk processing error | 1 retry immediately | Skip chunk, proceed with remaining audio |
| MedGemma 4B slow response | 1 retry with simplified prompt | After 2 failures, switch to deterministic FHIR fallback |

**Tier 2 — Graceful degradation (user informed, workflow continues):**

| Component Failure | Degraded Behaviour | User Sees |
|---|---|---|
| MedGemma 4B returns no/partial context | Generate letter from transcript only (no EHR enrichment) | Warning badge on S2: "Some records unavailable" |
| MedASR returns empty transcript | Prompt user to re-record or upload audio | Alert on S4: "Audio could not be transcribed" |
| FHIR server down entirely | All context panels show "EHR unavailable" | Warning on S2 + letter generated from transcript only |
| Section regeneration fails | Keep existing section text | Toast: "Could not regenerate. Original text preserved." |

**Tier 3 — Informative failure (user must act):**

| Failure | Error Message | Actions |
|---|---|---|
| MedGemma 27B OOM | "Document generation failed due to server memory. Please try again." | "Retry" button, "Return to Dashboard" |
| Audio file corrupted | "The audio file appears to be corrupted. Please re-record." | "Re-record", "Upload Audio File" |
| Pipeline timeout (>120s) | "Document generation is taking longer than expected." | "Retry", "Return to Dashboard" |
| GPU unavailable | "Clarke requires GPU acceleration which is currently unavailable." | "Return to Dashboard" |

### 10b. Error Response Format

All API errors return `ErrorResponse` (see §4 schema):

```json
{
  "error": "model_error",
  "message": "Document generation failed. Please try again.",
  "detail": "RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB",
  "consultation_id": "cons-uuid-xxxx",
  "timestamp": "2026-02-13T14:07:32Z"
}
```

- `message` is shown to the user.
- `detail` is logged but never shown to the user.

### 10c. Logging

```python
from loguru import logger

# Format: timestamp | level | component | message | context
logger.add(
    "logs/clarke_{time}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {extra[component]:<15} | {message}",
    rotation="50 MB",
    retention="7 days",
    level="DEBUG",
)

# Usage
logger.bind(component="medasr").info("Transcription complete", duration_s=12.3, word_count=245)
logger.bind(component="ehr_agent").error("FHIR query failed", patient_id="pt-001", exc_info=True)
```

Logs stored in `logs/` directory (not user-accessible). On HF Spaces, `print()` output goes to the Space's log tab.

---

## 11. Testing Specification

### 11a. Unit Tests

| Test File | What It Validates | Pass Criteria |
|---|---|---|
| `test_schemas.py` | All Pydantic models validate with valid data, reject invalid data | All valid fixtures pass validation; invalid fixtures raise `ValidationError` |
| `test_medasr.py` | Audio preprocessing (resample, mono conversion); mock transcription returns expected text | WAV output is 16kHz mono; mock returns correct transcript |
| `test_ehr_agent.py` | FHIR tool functions return valid JSON; output parser extracts JSON from messy output; deterministic fallback works | Tools return FHIR-compliant JSON; parser handles meta-commentary |
| `test_doc_generator.py` | Prompt template renders correctly with all variables; output parser splits sections; mock generation returns valid ClinicalDocument | Template contains transcript + context; parsed sections have headings |
| `test_fhir_client.py` | FHIR client constructs correct query URLs; handles 404 and timeout gracefully | URLs match expected patterns; errors return empty results, not exceptions |
| `test_api.py` | Each API endpoint returns correct status code and schema | `/health` → 200, `/patients` → 200 with list, `/consultations/start` → 201, etc. |

### 11b. Integration Tests

| Test | What It Validates | Pass Criteria |
|---|---|---|
| `test_e2e.py::test_full_pipeline` | Audio file → MedASR → transcript → EHR Agent → context → MedGemma 27B → document | Document contains both transcript content AND FHIR-sourced lab values |
| `test_e2e.py::test_mrs_thompson_scenario` | Mrs Thompson demo scenario produces clinically appropriate letter | Letter mentions HbA1c 55, eGFR 52, Penicillin allergy, gliclazide |
| `test_e2e.py::test_pipeline_timeout` | Pipeline respects 120s timeout and returns graceful error | Returns ErrorResponse with `error="timeout"` within 130s |
| `test_e2e.py::test_fhir_failure_degradation` | Pipeline continues when FHIR server is unreachable | Letter is generated from transcript only; context warnings present |

### 11c. Smoke Tests (Pre-Demo)

1. Open Clarke in incognito browser → dashboard loads with 5 patients.
2. Select Mrs. Thompson → context panel populates within 10s.
3. Click "Start Consultation" → play `mrs_thompson.wav` → click "End Consultation".
4. Letter appears within 60s containing HbA1c value from FHIR.
5. Edit one paragraph → Sign Off → status turns green.

---

## 12. Known Technical Pitfalls and Defensive Coding Requirements

### Pitfall 1: MedGemma 4B Instruction-Following Bugs

**Issue:** MedGemma 4B (`google/medgemma-1.5-4b-it`) is reported to leak system prompts into output, generate meta-commentary ("Here is the JSON you requested:"), output chain-of-thought training artifacts, and include special tokens in responses.

**Defensive coding:**
- **Always parse output with `parse_agent_output()`** (§6b) — never pass raw model output to downstream components.
- **Strip everything before the first `{` and after the last `}`** in JSON extraction.
- **Validate parsed JSON against the `PatientContext` Pydantic schema** — reject and retry if validation fails.
- **Implement deterministic FHIR fallback** in `backend/fhir/queries.py` — if agentic tool-calling fails after 2 attempts, switch to hardcoded FHIR queries + MedGemma 4B summarisation-only mode.
- **Test with ≥5 different patient scenarios** before declaring the agent working.

### Pitfall 2: MedGemma 27B VRAM Requirements

**Issue:** MedGemma 27B requires ~54GB VRAM unquantised. Even with 4-bit NF4 quantisation (~16GB), three models loaded simultaneously need ~19.5GB, leaving limited headroom on A100 40GB.

**Defensive coding:**
- **Always load with `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quant=True)`.**
- **Use `device_map="auto"`** to allow accelerate to manage memory.
- **Monitor VRAM before inference:** `torch.cuda.memory_allocated()`. If >35GB used, clear KV cache with `torch.cuda.empty_cache()` before generation.
- **For fine-tuning:** Unload MedASR and MedGemma 4B before training. Reload after.
- **Fallback path:** If 27B fails to load → try Ollama GGUF Q8_0 → if that fails → use 4B for generation.

### Pitfall 3: GPU Memory Management with Three Concurrent Models

**Issue:** MedASR, MedGemma 4B, and MedGemma 27B all on one GPU. KV cache growth during generation can cause OOM.

**Defensive coding:**
- **Sequential inference, not parallel.** Never run two models simultaneously.
- **Call `torch.cuda.empty_cache()`** between each model's inference step.
- **Set `max_new_tokens` conservatively** (2048 for 27B, 512 for 4B).
- **Implement OOM recovery in orchestrator:** catch `torch.cuda.OutOfMemoryError`, clear cache, reduce `max_new_tokens` by 50%, retry once.

### Pitfall 4: Gradio-Specific Limitations

**Issue:** Gradio has constraints around JavaScript interop, WebSocket support, and custom CSS injection.

**Defensive coding:**
- **Audio capture:** Use `gr.Audio(source="microphone")` as primary method. If JavaScript `MediaRecorder` interop is unreliable in Gradio 5.x, fall back to Gradio's native audio component (records complete audio, no streaming).
- **Custom CSS:** Inject via `gr.Blocks(css="frontend/assets/style.css")`. Test that CSS custom properties (`--clarke-blue`, etc.) apply correctly.
- **State management:** Use `gr.State` for consultation state. Test that state persists across event callbacks within a single session.
- **Inline editing:** Gradio doesn't natively support `contenteditable`. Use `gr.Textbox(interactive=True)` per section, or inject custom HTML with JavaScript for inline editing. Test editing works before committing to a pattern.

### Pitfall 5: HAPI FHIR Server in Docker-in-Docker

**Issue:** HF Spaces runs inside Docker. Running HAPI FHIR (another Docker container) inside that may not work.

**Defensive coding:**
- **Default to mock FHIR API** (`USE_MOCK_FHIR=true`) for HF Spaces deployment. The mock API serves identical data.
- **If HAPI FHIR is used:** Run as a separate process (not Docker-in-Docker). Use HAPI FHIR's embedded mode (Java JAR) or the Python mock as primary.
- **Decision point:** If FHIR server isn't running by end of Hour 2, switch to mock immediately.

### Pitfall 6: Audio Format Compatibility

**Issue:** Browser `MediaRecorder` outputs WebM/Opus. MedASR expects 16kHz mono WAV.

**Defensive coding:**
- **Always convert server-side** via `backend/audio.py` using pydub + ffmpeg.
- **Validate audio before passing to MedASR:** check sample rate = 16000, channels = 1, duration > 5s.
- **Handle empty/corrupted audio:** Return `ErrorResponse` with actionable message, not a raw exception.

---

*This document is the engineering blueprint for Clarke. Every directory, schema, endpoint, model configuration, and error path is defined here with enough specificity for Codex to implement without ambiguity. When a value can be specified exactly, it is. All specifications are consistent with clarke_PRD_masterplan.md (goals, constraints, risks), clarke_PRD_implementation.md (build sequence), clarke_PRD_design_guidelines.md (visual tokens referenced by frontend), and clarke_PRD_userflow.md (every screen and interaction mapped to a backend call). Uncertain decisions are flagged with fallback paths.*
