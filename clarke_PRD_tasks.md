# Clarke — PRD Tasks (Build Execution Plan)

**Version:** 1.0 | **Date:** 13 February 2026 | **Author:** Project Lead  
**Status:** Final — step-by-step execution plan for AI coding agent (Codex)  
**Parent document:** clarke_PRD_masterplan.md  
**Scope:** Ordered, atomic task list with verification criteria for every step of the Clarke build  
**Not in scope:** Strategic rationale (masterplan.md), visual styling (design_guidelines.md), user journey detail (userflow.md), architecture blueprints (technical_spec.md). Tasks reference these documents where needed.

---

## Summary Table

| Task | Title | Priority | Prerequisites | Est. Time |
|------|-------|----------|---------------|-----------|
| 0 | Read & Confirm Understanding | Core | None | 15 min |
| 1 | Create Project Directory Structure | Core | T0 | 15 min |
| 2 | Configuration & Environment Setup | Core | T1 | 20 min |
| 3 | Pydantic Data Models & Schemas | Core | T1 | 30 min |
| 4 | Synthetic FHIR Patient Data | Core | T3 | 45 min |
| 5 | Mock FHIR API Server | Core | T4 | 30 min |
| 6 | Demo Audio Files & Transcripts | Core | T1 | 30 min |
| 7 | **Phase 0 Checkpoint** | Core | T2,T5,T6 | 10 min |
| 8 | MedASR Model Loading & Audio Preprocessing | Core | T7 | 30 min |
| 9 | MedASR Transcription Pipeline | Core | T8 | 30 min |
| 10 | FHIR Client & Tool Functions | Core | T5 | 30 min |
| 11 | MedGemma 4B EHR Agent — Loading & Context Retrieval | Core | T10 | 45 min |
| 12 | Orchestrator — Pipeline Coordinator | Core | T9,T11 | 45 min |
| 13 | Prompt Templates (EHR Agent + Document Generation) | Core | T12 | 30 min |
| 14 | **Phase 1 Checkpoint — Integration Test Point 1** | Core | T13 | 20 min |
| 15 | MedGemma 27B Loading & Baseline Generation | Core | T14 | 45 min |
| 16 | Document Generation Prompt Engineering | Core | T15 | 30 min |
| 17 | End-to-End Backend Pipeline Wiring | Core | T16 | 30 min |
| 18 | Pipeline Hardening — Error Handling & Timeouts | Core | T17 | 30 min |
| 19 | **Phase 2 Checkpoint** | Core | T18 | 15 min |
| 20 | Gradio Theme & CSS Setup | Core | T19 | 30 min |
| 21 | Gradio UI — Core Layout & Dashboard (S1) | Core | T20 | 45 min |
| 22 | Gradio UI — Patient Context & Recording (S2, S3) | Core | T21 | 45 min |
| 23 | Gradio UI — Processing, Review & Sign-off (S4, S5, S6) | Core | T22 | 45 min |
| 24 | UI ↔ Backend Data Binding | Core | T23 | 45 min |
| 25 | End-to-End Demo Scenario Testing (3 patients) | Core | T24 | 30 min |
| 26 | **Phase 3 Checkpoint — Integration Test Point 2** | Core | T25 | 20 min |
| 27 | Synthetic Training Data Generation | Polish | T26 | 45 min |
| 28 | LoRA Fine-tuning MedGemma 27B | Polish | T27 | 90 min |
| 29 | MedASR Evaluation (WER) | Polish | T26 | 30 min |
| 30 | EHR Agent Evaluation (Fact Recall) | Polish | T26 | 30 min |
| 31 | Document Generation Evaluation (BLEU/ROUGE-L) | Polish | T28 or T26 | 30 min |
| 32 | UI Visual Polish | Polish | T26 | 45 min |
| 33 | **Phase 4 Checkpoint** | Core | T26 + any completed T27–T32 | 15 min |
| 34 | HF Space Deployment | Core | T33 | 45 min |
| 35 | HF Hub LoRA Adapter Publication | Polish | T28,T34 | 20 min |
| 36 | GitHub Repo & README | Core | T34 | 45 min |
| 37 | Final Smoke Test & Submission Checklist | Core | T36 | 30 min |
| 38 | **Phase 5 Checkpoint — Final** | Core | T37 | 15 min |

**Total: 39 tasks. Estimated: ~20 hours of active work + 4 hours buffer.**

---

## PHASE 0 — Environment & Data Foundation (Hours 1–3)

**Phase goal:** Running project with configuration, synthetic FHIR data, mock FHIR API, and demo audio assets — everything downstream tasks depend on.  
**Estimated time:** 3 hours  
**Day-end checkpoint contribution:** Provides foundation for Day 1 (Hours 1–8).  
**Context required:** `clarke_PRD_technical_spec.md` (§1–§3, §7–§8).

---

### Task 0: Read & Confirm Understanding

**Prerequisites:** None  
**Priority:** Core

**Description:**  
Before writing any code, read ALL of the following PRD files completely:
1. `clarke_PRD_masterplan.md` — vision, goals, constraints, success criteria
2. `clarke_PRD_implementation.md` — build phases, time allocation, dependency graph, fallback paths
3. `clarke_PRD_design_guidelines.md` — colour tokens, typography, spacing, animations
4. `clarke_PRD_userflow.md` — screens, states, navigation, demo golden path
5. `clarke_PRD_technical_spec.md` — directory tree, tech stack, data models, API contracts, model serving

After reading, output a structured summary demonstrating comprehension:
- **Product vision** (1–2 sentences from masterplan)
- **Number of screens** to build (from userflow)
- **Number of API endpoints** (from technical_spec §5)
- **The three HAI-DEF models**, their HuggingFace IDs, and their roles in the pipeline
- **Top 3 technical risks** and their fallback paths (from masterplan §8)
- **Must-have list** (from masterplan §12) — list all 10 items

**Files created or modified:** None  
**"Done" criteria:** Summary is output and contains all 6 items listed above with correct details.  
**Verification method:** Manual review of output. Spot-check: MedGemma 4B model ID should be `google/medgemma-1.5-4b-it` (not 1.0). Number of screens should be 6 (S1–S6). Number of API endpoints should be 12.  
**If this fails:** Re-read the specific PRD where the information was missed.

---

### Task 1: Create Project Directory Structure

**Prerequisites:** Task 0  
**Priority:** Core

**Description:**  
Create the complete Clarke project directory tree exactly as defined in `clarke_PRD_technical_spec.md` §1. Create all directories and empty `__init__.py` files. Create placeholder files (empty or with a single docstring comment) for every file listed in the tree.

The top-level directory is `clarke/`. Key subdirectories:
- `backend/` — orchestrator, api, config, models/, fhir/, prompts/, schemas, audio, errors, utils
- `frontend/` — ui, theme, components, state, assets/
- `data/` — synthea/, fhir_bundles/, demo/, training/
- `finetuning/` — train_lora, generate_training_data, merge_adapter
- `evaluation/` — eval_medasr, eval_ehr_agent, eval_doc_gen, gold_standards/
- `tests/` — test files for each component
- `scripts/` — start.sh, health_check.sh, setup_fhir.sh
- Root files: app.py, Dockerfile, requirements.txt, .env.template, README.md, LICENSE

**Files created or modified:** All files and directories in the tree (~60 files).  
**"Done" criteria:** The directory tree matches `clarke_PRD_technical_spec.md` §1 exactly. All `__init__.py` files exist. All placeholder files exist.  
**Verification method:** `find clarke/ -type f | sort` output matches the spec tree. `python -c "import backend; import frontend"` succeeds (empty packages import fine).  
**If this fails:** Compare find output to spec tree line-by-line and create missing files.

---

### Task 2: Configuration & Environment Setup

**Prerequisites:** Task 1  
**Priority:** Core

**Description:**  
2a. **`.env.template`** — Populate with all environment variables from `clarke_PRD_technical_spec.md` §3a. Include every variable with its default value and comment.

2b. **`backend/config.py`** — Create a centralised configuration module using `pydantic-settings` (or `python-dotenv` + dataclass). Load all env vars from `.env`. Include defaults matching the `.env.template`. Key config values:
- Model IDs: `MEDASR_MODEL_ID=google/medasr`, `MEDGEMMA_4B_MODEL_ID=google/medgemma-1.5-4b-it`, `MEDGEMMA_27B_MODEL_ID=google/medgemma-27b-text-it`
- FHIR: `FHIR_SERVER_URL=http://localhost:8080/fhir`, `USE_MOCK_FHIR=true`, `FHIR_TIMEOUT_S=10`
- App: `APP_PORT=7860`, `PIPELINE_TIMEOUT_S=120`, `DOC_GEN_MAX_TOKENS=2048`, `DOC_GEN_TEMPERATURE=0.3`
- Fine-tuning: `LORA_RANK=16`, `LORA_ALPHA=32`, `LEARNING_RATE=2e-4`, `TRAINING_EPOCHS=3`

2c. **`requirements.txt`** — List all dependencies with pinned versions from `clarke_PRD_technical_spec.md` §2. Include: torch, transformers, bitsandbytes, accelerate, peft, trl, datasets, gradio, fastapi, uvicorn, httpx, pydub, librosa, jinja2, jiwer, rouge_score, sacrebleu, reportlab, wandb, huggingface_hub, python-dotenv, loguru, pydantic.

2d. **`Dockerfile`** — Create the Dockerfile exactly as specified in `clarke_PRD_technical_spec.md` §3b.

2e. **`LICENSE`** — Apache 2.0 licence file.

2f. **`backend/errors.py`** — Create custom exception classes and logging configuration using loguru (see `clarke_PRD_technical_spec.md` §10c).

2g. **`backend/utils.py`** — Create shared utilities: timing decorator, JSON sanitisation function.

**Files created or modified:** `.env.template`, `backend/config.py`, `requirements.txt`, `Dockerfile`, `LICENSE`, `backend/errors.py`, `backend/utils.py`  
**"Done" criteria:** `python -c "from backend.config import Settings; s = Settings(); print(s.MEDASR_MODEL_ID)"` prints `google/medasr`. All files exist and contain the specified content.  
**Verification method:** Run the Python import command above. `cat requirements.txt | grep transformers` returns a version. `cat Dockerfile | grep nvidia` returns the CUDA base image line.  
**If this fails:** Debug import errors. Ensure `.env` file exists (copy from `.env.template`).

---

### Task 3: Pydantic Data Models & Schemas

**Prerequisites:** Task 1  
**Priority:** Core

**Description:**  
Implement ALL Pydantic v2 data models in `backend/schemas.py` exactly as defined in `clarke_PRD_technical_spec.md` §4. This includes:

- **Enums:** `ConsultationStatus` (idle, recording, paused, processing, review, signed_off), `PipelineStage` (transcribing, retrieving_context, generating_document, complete, failed)
- **Models:** `Patient`, `LabResult`, `PatientContext`, `Transcript`, `DocumentSection`, `ClinicalDocument`, `Consultation`, `PipelineProgress`, `ErrorResponse`

Copy the exact field definitions, types, descriptions, and defaults from §4. Include all docstrings.

Also create `tests/test_schemas.py`:
- Test that each model validates with valid fixture data.
- Test that each model rejects invalid data (wrong types, missing required fields).
- Test enum values are correct.

**Files created or modified:** `backend/schemas.py`, `tests/test_schemas.py`  
**"Done" criteria:** `pytest tests/test_schemas.py` passes with 0 failures.  
**Verification method:** `pytest tests/test_schemas.py -v`  
**If this fails:** Check field types and defaults against the spec. Common issue: `list[str]` syntax requires `from __future__ import annotations`.

---

### Task 4: Synthetic FHIR Patient Data

**Prerequisites:** Task 3  
**Priority:** Core

**Description:**  
Create FHIR Bundle JSON files for 5 demo patients in `data/fhir_bundles/`. These are pre-built JSON files that the mock FHIR API will serve. Each patient needs:

- **Patient resource** (demographics, NHS number, GP) — format per `clarke_PRD_technical_spec.md` §8c
- **Condition resources** (active diagnoses with SNOMED codes) — format per §8f
- **MedicationRequest resources** (current medications with BNF names, doses)
- **Observation resources** (recent lab results with LOINC codes, mmol/L units, reference ranges) — format per §8d
- **AllergyIntolerance resources** (allergies with reactions, severity) — format per §8e
- **DiagnosticReport resources** (imaging/reports)

Create one JSON Bundle file per patient: `pt-001.json` through `pt-005.json`.

**The 5 demo patients** (from `clarke_PRD_technical_spec.md` §8b):

| ID | Name | Age/Sex | Scenario | Key Data |
|---|---|---|---|---|
| pt-001 | Mrs. Margaret Thompson | 67F | T2DM, rising HbA1c | HbA1c 55 mmol/mol (was 48), eGFR 52, Penicillin allergy, Metformin 1g BD, Gliclazide 40mg OD |
| pt-002 | Mr. Emeka Okafor | 54M | Chest pain post-angiography | Normal coronaries, Troponin negative, BP 148/92, Aspirin 75mg, Atorvastatin 40mg |
| pt-003 | Ms. Priya Patel | 28F | Asthma review | Peak flow 320 (pred 450), Salbutamol 4x/week, no preventer currently |
| pt-004 | Mr. David Williams | 72M | Heart failure review | EF 35%, BNP 450 pg/mL, Bisoprolol 5mg, Ramipril 5mg, Furosemide 40mg |
| pt-005 | Mrs. Fatima Khan | 45F | Depression follow-up | PHQ-9 score 12, Sertraline 100mg |

Also create `data/clinic_list.json` exactly as specified in `clarke_PRD_technical_spec.md` §8h.

**Files created or modified:** `data/fhir_bundles/pt-001.json` through `pt-005.json`, `data/clinic_list.json`  
**"Done" criteria:** All 5 JSON files are valid JSON. Each contains at minimum: 1 Patient, 2+ Conditions, 2+ MedicationRequests, 3+ Observations, 1+ AllergyIntolerance. `data/clinic_list.json` lists all 5 patients. `python -c "import json; [json.load(open(f'data/fhir_bundles/pt-00{i}.json')) for i in range(1,6)]"` succeeds.  
**Verification method:** Run the Python JSON validation command above. Manually inspect `pt-001.json` to confirm Mrs Thompson has HbA1c=55, eGFR=52, Penicillin allergy.  
**If this fails:** Fix JSON syntax errors. Ensure FHIR resource structure matches the examples in technical_spec §8c–§8f.

---

### Task 5: Mock FHIR API Server

**Prerequisites:** Task 4  
**Priority:** Core

**Description:**  
Implement `backend/fhir/mock_api.py` — a FastAPI application that serves FHIR-like REST endpoints using the pre-built JSON files from `data/fhir_bundles/`. This is the default for development and HF Spaces deployment (`USE_MOCK_FHIR=true`).

Endpoints to implement (mirroring HAPI FHIR patterns from `clarke_PRD_technical_spec.md` §7c):

```
GET /fhir/Patient/{patient_id}           → returns Patient resource
GET /fhir/Patient?name={name}&_count=10  → search patients by name
GET /fhir/Condition?patient={id}&clinical-status=active → patient conditions
GET /fhir/MedicationRequest?patient={id}&status=active → patient medications
GET /fhir/Observation?patient={id}&category=laboratory&_sort=-date&_count=20 → lab results
GET /fhir/AllergyIntolerance?patient={id} → patient allergies
GET /fhir/DiagnosticReport?patient={id}&_sort=-date&_count=5 → reports
GET /fhir/Encounter?patient={id}&_sort=-date&_count=3 → recent encounters
```

The mock API loads all JSON bundles from `data/fhir_bundles/` at startup and indexes them by patient ID and resource type. Each endpoint filters and returns the appropriate resources in FHIR Bundle format.

Also create `tests/test_fhir_client.py` to test:
- Each endpoint returns 200 with valid FHIR JSON for known patients.
- Unknown patient returns 404 or empty Bundle.
- Endpoints handle query parameters correctly (patient filter, _count, _sort).

**Files created or modified:** `backend/fhir/mock_api.py`, `tests/test_fhir_client.py`  
**"Done" criteria:** Mock FHIR API starts and responds correctly to all 8 endpoint patterns. `pytest tests/test_fhir_client.py` passes.  
**Verification method:** Start the mock API (`python -m backend.fhir.mock_api &`), then: `curl http://localhost:8080/fhir/Patient/pt-001` returns Mrs Thompson's Patient resource with NHS number. `curl "http://localhost:8080/fhir/Observation?patient=pt-001&category=laboratory"` returns observations including HbA1c.  
**If this fails:** Check JSON loading paths. Ensure Bundle files have correct resource indexing. Verify FastAPI route parameter parsing.

---

### Task 6: Demo Audio Files & Ground-Truth Transcripts

**Prerequisites:** Task 1  
**Priority:** Core

**Description:**  
Create 3 demo audio files and their corresponding ground-truth transcripts:

6a. **Ground-truth transcripts** — Create text files in `data/demo/`:
- `mrs_thompson_transcript.txt` — ~200 words. Simulated diabetes clinic consultation. Must mention: HbA1c, fatigue, thirst, gliclazide discussion, metformin continuation, blood test follow-up in 3 months.
- `mr_okafor_transcript.txt` — ~200 words. Chest pain follow-up. Must mention: angiogram results, normal coronaries, reassurance, blood pressure management, lifestyle advice.
- `ms_patel_transcript.txt` — ~200 words. Asthma review. Must mention: peak flow, salbutamol overuse, inhaler technique, preventer inhaler recommendation.

6b. **Audio files** — Generate WAV audio files (16kHz, mono, 60–90 seconds) for each transcript. Options:
- **Preferred:** Use a TTS engine (e.g., `edge-tts` or `gtts`) to generate speech from the transcripts, then convert with: `ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav`
- **Fallback:** Create minimal valid WAV files with silence + a note that real audio will be recorded separately for the video.

Place files at: `data/demo/mrs_thompson.wav`, `data/demo/mr_okafor.wav`, `data/demo/ms_patel.wav`

**Files created or modified:** `data/demo/mrs_thompson_transcript.txt`, `data/demo/mr_okafor_transcript.txt`, `data/demo/ms_patel_transcript.txt`, `data/demo/mrs_thompson.wav`, `data/demo/mr_okafor.wav`, `data/demo/ms_patel.wav`  
**"Done" criteria:** All 3 transcript files exist with ≥150 words each. All 3 WAV files exist, are valid audio, and are 16kHz mono. `ffprobe data/demo/mrs_thompson.wav` shows `16000 Hz, mono`.  
**Verification method:** `wc -w data/demo/*_transcript.txt` shows ≥150 per file. `python -c "import librosa; y, sr = librosa.load('data/demo/mrs_thompson.wav', sr=None); assert sr == 16000; print(f'Duration: {len(y)/sr:.1f}s')"` succeeds.  
**If this fails:** Re-run ffmpeg conversion with correct flags. If TTS fails, generate silence WAV: `ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 60 -acodec pcm_s16le output.wav`.

---

### Task 7: Phase 0 Checkpoint

**Prerequisites:** Tasks 2, 5, 6  
**Priority:** Core

**Description:**  
Run the complete Phase 0 verification suite. Confirm all foundation components are in place before proceeding to model pipeline work.

Verification checklist:
1. Project directory structure matches spec (`find clarke/ -type f | wc -l` ≥ 50 files).
2. `python -c "from backend.config import Settings; s = Settings(); print(s.MEDASR_MODEL_ID)"` prints `google/medasr`.
3. `pytest tests/test_schemas.py` passes.
4. Mock FHIR API starts and `curl http://localhost:8080/fhir/Patient/pt-001` returns valid JSON.
5. `data/clinic_list.json` has 5 patients.
6. 3 WAV files exist in `data/demo/` and are 16kHz mono.
7. 3 transcript files exist in `data/demo/`.

**Files created or modified:** None  
**"Done" criteria:** All 7 checks pass.  
**Verification method:** Run each check command above sequentially. Report pass/fail for each.  
**If this fails:** Fix the specific failing check, then re-run the entire checkpoint.

---

## PHASE 1 — Core Model Pipelines (Hours 4–8)

**Phase goal:** MedASR transcription pipeline + MedGemma 4B EHR agent + orchestrator connecting them. Backend-only — no UI yet.  
**Estimated time:** 5 hours  
**Day-end checkpoint contribution:** Completes Day 1 checkpoint (all 6 items from implementation.md §5).  
**Context required:** `clarke_PRD_technical_spec.md` (§6a–§6b, §7, §9), `clarke_PRD_implementation.md` (§2–§3 Phase 1).

---

### Task 8: MedASR Model Loading & Audio Preprocessing

**Prerequisites:** Task 7  
**Priority:** Core

**Description:**  
8a. **`backend/audio.py`** — Implement audio format conversion utilities:
- `convert_to_wav_16k(input_path: str, output_path: str) -> str` — Converts any audio format (WebM, MP3, etc.) to 16kHz mono WAV using pydub + ffmpeg. Exactly as specified in `clarke_PRD_technical_spec.md` §9e.
- `validate_audio(file_path: str) -> dict` — Checks: sample rate = 16000, channels = 1, duration > 5s and < 1800s. Returns dict with duration_s, sample_rate, channels. Raises `AudioError` on failure.

8b. **`backend/models/model_manager.py`** — Implement shared model lifecycle:
- `ModelManager` class that tracks loaded models, monitors GPU VRAM (`torch.cuda.memory_allocated()`), and provides `clear_cache()` (calls `torch.cuda.empty_cache()`).
- Method `check_gpu()` — returns GPU name, VRAM used, VRAM total. Returns mock data if no GPU.

8c. **`backend/models/medasr.py`** — Implement MedASR loading:
- Load model using `transformers.pipeline("automatic-speech-recognition", model="google/medasr", device="cuda:0")` — or return mock if `MEDASR_MODEL_ID == "mock"`.
- `load_model()` — loads the pipeline. Called once at startup.
- `transcribe(audio_path: str) -> Transcript` — loads audio via librosa at 16kHz, runs pipeline with `chunk_length_s=20, stride_length_s=(4, 2), return_timestamps=True`. Returns `Transcript` schema.
- **Mock mode:** If model ID is "mock", return the ground-truth transcript from `data/demo/{patient}_transcript.txt` for known demo files, or a generic placeholder for unknown audio.

**Files created or modified:** `backend/audio.py`, `backend/models/model_manager.py`, `backend/models/medasr.py`, `tests/test_medasr.py`  
**"Done" criteria:** In mock mode: `python -c "from backend.models.medasr import MedASRModel; m = MedASRModel(); t = m.transcribe('data/demo/mrs_thompson.wav'); print(t.text[:50])"` prints the first 50 chars of the Thompson transcript. Audio conversion: converting a test file produces valid 16kHz mono WAV.  
**Verification method:** Run the Python command above. `pytest tests/test_medasr.py` passes (test mock mode + audio validation).  
**If this fails:** Check librosa/pydub installation. If GPU not available, ensure mock mode activates correctly based on config.

---

### Task 9: MedASR Transcription Pipeline

**Prerequisites:** Task 8  
**Priority:** Core

**Description:**  
Create the FastAPI transcription endpoint and wire it to MedASR.

9a. **`backend/api.py`** — Add these endpoints (from `clarke_PRD_technical_spec.md` §5):
- `GET /api/v1/health` — Returns system health status including model loaded states and FHIR status. Schema per §5b.
- `POST /api/v1/consultations/{id}/audio` — Accepts multipart form-data with `audio_file` (WAV or WebM) and `is_final` boolean. Saves audio, converts to 16kHz WAV if needed, returns duration.

9b. Wire the `/audio` endpoint to call `backend/audio.py` for conversion and store the audio file path in an in-memory consultation store (dict keyed by consultation ID).

9c. Create `tests/test_api.py` — Test `/health` returns 200 with correct schema. Test `/consultations/{id}/audio` accepts a WAV file and returns duration.

**Files created or modified:** `backend/api.py`, `tests/test_api.py`  
**"Done" criteria:** FastAPI app starts. `curl localhost:8000/api/v1/health` returns 200 with JSON containing `models` key. Uploading a WAV file to `/consultations/test-001/audio` returns 200 with `duration_s`.  
**Verification method:** Start FastAPI (`uvicorn backend.api:app --port 8000 &`), run curl commands, `pytest tests/test_api.py`.  
**If this fails:** Check FastAPI route definitions. Ensure multipart form handling is correct.

---

### Task 10: FHIR Client & Tool Functions

**Prerequisites:** Task 5  
**Priority:** Core

**Description:**  
10a. **`backend/fhir/client.py`** — Implement async FHIR REST client using httpx:
- `FHIRClient` class initialised with `fhir_server_url` and `timeout_s` from config.
- Async methods for each FHIR query pattern from `clarke_PRD_technical_spec.md` §7c.
- Handle 404 (return empty), timeout (raise with context), 5xx (retry once, then raise).
- Return raw JSON dicts.

10b. **`backend/fhir/tools.py`** — Implement the 7 FHIR tool functions specified in `clarke_PRD_technical_spec.md` §6b:
```python
async def search_patients(name: str) -> list[dict]
async def get_conditions(patient_id: str) -> list[dict]
async def get_medications(patient_id: str) -> list[dict]
async def get_observations(patient_id: str, category: str = "laboratory") -> list[dict]
async def get_allergies(patient_id: str) -> list[dict]
async def get_diagnostic_reports(patient_id: str) -> list[dict]
async def get_recent_encounters(patient_id: str) -> list[dict]
```
Each wraps a `FHIRClient` call and extracts the relevant entries from the Bundle response.

10c. **`backend/fhir/queries.py`** — Implement deterministic FHIR query fallback:
- `get_full_patient_context(patient_id: str) -> dict` — Calls ALL 7 tool functions for a patient and aggregates results into a raw context dict. This is the fallback if MedGemma 4B agentic tool-calling fails.

**Files created or modified:** `backend/fhir/client.py`, `backend/fhir/tools.py`, `backend/fhir/queries.py`  
**"Done" criteria:** With mock FHIR running: `python -c "import asyncio; from backend.fhir.queries import get_full_patient_context; r = asyncio.run(get_full_patient_context('pt-001')); print(list(r.keys()))"` prints keys including conditions, medications, observations, allergies.  
**Verification method:** Run the Python command above. Each key should contain non-empty lists for pt-001.  
**If this fails:** Check mock FHIR is running. Verify URL construction in client.py matches mock API routes.

---

### Task 11: MedGemma 4B EHR Agent — Loading & Context Retrieval

**Prerequisites:** Task 10  
**Priority:** Core

**Description:**  
Implement the EHR context retrieval agent in `backend/models/ehr_agent.py`.

**Primary implementation (deterministic FHIR + MedGemma 4B summarisation):**

Given the known instruction-following bugs with MedGemma 4B (see `clarke_PRD_technical_spec.md` §12, Pitfall 1), start with the **deterministic fallback** approach — it's more reliable and the narrative still works:

1. Call `get_full_patient_context(patient_id)` from `backend/fhir/queries.py` to retrieve all raw FHIR data.
2. Load MedGemma 4B in 4-bit quantised mode (config from `clarke_PRD_technical_spec.md` §6b):
   ```python
   bnb_config = BitsAndBytesConfig(
       load_in_4bit=True, bnb_4bit_quant_type="nf4",
       bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True
   )
   ```
3. Pass raw FHIR JSON to MedGemma 4B with the context synthesis prompt (from `backend/prompts/context_synthesis.j2`) asking it to produce a structured `PatientContext` JSON.
4. Parse output using `parse_agent_output()` from `clarke_PRD_technical_spec.md` §6b — strip system prompt leaks, extract JSON, validate against `PatientContext` schema.
5. If parsing fails after 2 retries, construct `PatientContext` directly from raw FHIR data without MedGemma summarisation (hardcoded extraction logic).

**Mock mode:** If model ID is "mock", return a pre-built PatientContext JSON for known patient IDs.

Also implement `parse_agent_output(raw_output: str) -> dict` exactly as specified in §6b — with regex to strip system prompt leaks, markdown fences, and extract first JSON object.

**Files created or modified:** `backend/models/ehr_agent.py`, `tests/test_ehr_agent.py`  
**"Done" criteria:** In mock mode: calling `get_patient_context("pt-001")` returns a valid `PatientContext` with Mrs Thompson's data (problem_list includes diabetes, medications include metformin, allergies include penicillin). `pytest tests/test_ehr_agent.py` passes.  
**Verification method:** `python -c "from backend.models.ehr_agent import EHRAgent; a = EHRAgent(); ctx = a.get_patient_context('pt-001'); print(ctx.allergies)"` outputs penicillin allergy data.  
**If this fails:** Check FHIR data loading. Verify parse_agent_output handles edge cases. If MedGemma 4B outputs are garbled, the hardcoded extraction fallback should still produce valid context.

**⚠️ FALLBACK DECISION POINT:** If MedGemma 4B produces entirely unusable output after loading (not just in mock mode, but on real inference), stay with deterministic FHIR extraction. The pipeline narrative is preserved — MedGemma 4B is still "understanding" the EHR data through the summarisation step. See `clarke_PRD_implementation.md` §7, Fallback Path #2.

---

### Task 12: Orchestrator — Pipeline Coordinator

**Prerequisites:** Tasks 9, 11  
**Priority:** Core

**Description:**  
Implement `backend/orchestrator.py` — the core pipeline coordinator that connects all three model stages.

The orchestrator manages the consultation lifecycle:
1. **start_consultation(patient_id)** — Creates a Consultation object, triggers EHR agent in background to pre-fetch patient context, returns consultation ID. Sets status to `recording`.
2. **end_consultation(consultation_id)** — Stops recording, runs the full pipeline:
   - Stage 1: Finalise transcript via MedASR (from uploaded audio)
   - Stage 2: Synthesise patient context via EHR Agent (may already be cached from start)
   - Stage 3: Combine transcript + context into document-generation prompt (Phase 2 will add MedGemma 27B generation)
   - Updates `PipelineProgress` at each stage
3. **get_consultation(consultation_id)** — Returns current Consultation state.
4. **get_progress(consultation_id)** — Returns current PipelineProgress.

Wire the remaining API endpoints from `clarke_PRD_technical_spec.md` §5:
- `GET /api/v1/patients` — returns clinic list from `data/clinic_list.json`
- `GET /api/v1/patients/{patient_id}` — returns single patient
- `POST /api/v1/patients/{patient_id}/context` — triggers EHR agent
- `POST /api/v1/consultations/start` — calls orchestrator.start_consultation
- `POST /api/v1/consultations/{id}/end` — calls orchestrator.end_consultation
- `GET /api/v1/consultations/{id}/transcript` — returns transcript
- `GET /api/v1/consultations/{id}/document` — returns document (empty for now)
- `GET /api/v1/consultations/{id}/progress` — returns pipeline progress

In-memory consultation store: `dict[str, Consultation]` keyed by consultation_id.

**Files created or modified:** `backend/orchestrator.py`, `backend/api.py` (update with all endpoints)  
**"Done" criteria:** Start mock FHIR + FastAPI. Calling `POST /consultations/start` with `{"patient_id": "pt-001"}` returns 201 with consultation_id. Calling `POST /consultations/{id}/audio` with a WAV file, then `POST /consultations/{id}/end` triggers the pipeline and returns 202. `GET /consultations/{id}/progress` shows stage transitions.  
**Verification method:** `pytest tests/test_api.py` passes (update tests for new endpoints). Manual curl sequence through the flow.  
**If this fails:** Debug orchestrator state management. Ensure consultation store is correctly updated at each stage.

---

### Task 13: Prompt Templates (EHR Agent + Document Generation)

**Prerequisites:** Task 12  
**Priority:** Core

**Description:**  
Create the Jinja2 prompt templates that combine transcript and context for document generation.

13a. **`backend/prompts/ehr_agent_system.txt`** — The EHR agent system prompt, exactly as specified in `clarke_PRD_technical_spec.md` §6b. This instructs MedGemma 4B on how to synthesise FHIR data into PatientContext JSON.

13b. **`backend/prompts/context_synthesis.j2`** — Jinja2 template that wraps raw FHIR data and asks MedGemma 4B to produce structured context JSON. Variables: `{{ raw_fhir_data }}`, `{{ patient_id }}`.

13c. **`backend/prompts/document_generation.j2`** — The document generation prompt template exactly as specified in `clarke_PRD_technical_spec.md` §6c. This is the prompt sent to MedGemma 27B. Variables: `{{ letter_date }}`, `{{ clinician_name }}`, `{{ clinician_title }}`, `{{ transcript }}`, `{{ context_json }}`.

Verify that the orchestrator can render the document generation prompt by combining a mock transcript and mock context into the template.

**Files created or modified:** `backend/prompts/ehr_agent_system.txt`, `backend/prompts/context_synthesis.j2`, `backend/prompts/document_generation.j2`  
**"Done" criteria:** `python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('backend/prompts')); t = env.get_template('document_generation.j2'); print(t.render(letter_date='13 Feb 2026', clinician_name='Dr. Chen', clinician_title='Consultant', transcript='test', context_json='{}')[:100])"` prints the rendered prompt start.  
**Verification method:** Run the command above. The output should contain "NHS clinical documentation assistant" and the rendered transcript.  
**If this fails:** Check template syntax. Ensure Jinja2 variables match the expected names.

---

### Task 14: Phase 1 Checkpoint — Integration Test Point 1

**Prerequisites:** Task 13  
**Priority:** Core

**Description:**  
This is **Integration Test Point 1** from `clarke_PRD_implementation.md` §8. Run the Mrs Thompson demo scenario end-to-end through the backend (no UI yet):

1. Feed `data/demo/mrs_thompson.wav` to MedASR → capture transcript.
2. Feed patient ID `pt-001` to EHR Agent → capture context JSON.
3. Combine into document-generation prompt → print to console.
4. **Verify the combined prompt contains:**
   - (a) Transcript text mentioning HbA1c, fatigue, gliclazide
   - (b) FHIR-sourced values: HbA1c 55 mmol/mol, eGFR 52, Penicillin allergy

This can run in mock mode — the point is verifying the *fusion* of transcript + context into a well-formed prompt.

Create `tests/test_e2e.py` with a test for this scenario.

Also run the full test suite: `pytest tests/` to confirm no regressions.

**Files created or modified:** `tests/test_e2e.py` (add `test_mrs_thompson_fusion`)  
**"Done" criteria:** The rendered document-generation prompt contains both: (1) transcript text with clinical content, and (2) FHIR-sourced patient context with lab values, medications, and allergies. `pytest tests/ -v` passes with 0 failures.  
**Verification method:** `pytest tests/test_e2e.py::test_mrs_thompson_fusion -v` passes. Manually inspect printed prompt output.  
**If this fails:** Debug which stage produced empty output. If transcript is empty, check MedASR mock. If context is empty, check FHIR mock data loading. If prompt is malformed, check Jinja2 template rendering.

**📌 DAY 1 DECISION POINT:** If this checkpoint fails, do NOT proceed to Phase 2. Fix the fusion point first — everything downstream depends on it.

---

## PHASE 2 — Document Generation & End-to-End Pipeline (Hours 9–12)

**Phase goal:** MedGemma 27B loaded and generating clinic letters. Complete backend pipeline: audio → transcript → context → letter.  
**Estimated time:** 4 hours  
**Day-end checkpoint contribution:** Achieves Minimum Viable Demo backend (implementation.md §6).  
**Context required:** `clarke_PRD_technical_spec.md` (§6c, §10), `clarke_PRD_implementation.md` (§3 Phase 2).

---

### Task 15: MedGemma 27B Loading & Baseline Generation

**Prerequisites:** Task 14  
**Priority:** Core

**Description:**  
Implement `backend/models/doc_generator.py` — the document generation module using MedGemma 27B.

**Loading (from `clarke_PRD_technical_spec.md` §6c):**
```python
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True
)
model = AutoModelForCausalLM.from_pretrained(
    "google/medgemma-27b-text-it", quantization_config=bnb_config,
    device_map="auto", torch_dtype=torch.bfloat16
)
```

**Generation parameters:** `max_new_tokens=2048, temperature=0.3, top_p=0.9, top_k=40, do_sample=True, repetition_penalty=1.1`

**Interface:**
- `load_model()` — loads model + tokenizer. If model ID is "mock", set flag.
- `generate(prompt: str) -> str` — runs inference, returns raw text.
- `generate_document(transcript: str, context: PatientContext) -> ClinicalDocument` — renders the Jinja2 prompt, calls generate, parses output into ClinicalDocument sections.
- **Output parsing:** Split generated text into `DocumentSection` objects by detecting section headings.
- **Mock mode:** Return a pre-written reference letter.

**Timeout:** 90s. **Retry:** 1 retry with reduced `max_new_tokens=1024`.

Generate 3 baseline letters using the combined prompts from Task 13 (one per demo patient). Save to `data/demo/baseline_letters/`.

**Files created or modified:** `backend/models/doc_generator.py`, `tests/test_doc_generator.py`, `data/demo/baseline_letters/` (3 files)  
**"Done" criteria:** In mock mode: `generate_document()` returns a valid `ClinicalDocument` with ≥4 sections. On GPU: MedGemma 27B loads without OOM and generates coherent medical text. `pytest tests/test_doc_generator.py` passes.  
**Verification method:** Run tests. On GPU, generate one letter and manually verify it's coherent medical text.  
**If this fails:** **⚠️ FALLBACK TRIGGER:** If MedGemma 27B fails to load after 2 attempts (OOM on A100 40GB at 4-bit):
1. Try GGUF Q8_0 via Ollama — switch inference to Ollama REST API. See `clarke_PRD_implementation.md` §7, Fallback Path A.
2. If Ollama also fails — use MedGemma 4B for document generation with extensive prompt engineering. This changes Tasks 16–17 to use 4B instead of 27B. Quality drops but pipeline remains functional.

---

### Task 16: Document Generation Prompt Engineering

**Prerequisites:** Task 15  
**Priority:** Core

**Description:**  
Iterate on the document-generation prompt to maximise NHS letter quality:

1. Start with the base prompt from `backend/prompts/document_generation.j2`.
2. Generate 3 letters (one per demo patient) using the base prompt.
3. Review each letter for:
   - NHS letter structure (date, addressee, Re: line, salutation, sections, sign-off)
   - Correct use of FHIR-sourced lab values (exact numbers, not fabricated)
   - British medical English (third person, past tense, formal)
   - Reasonable length (300–500 words)
4. Iterate on the prompt: add exemplar fragments, strengthen format instructions, add negative examples (what NOT to do).
5. Regenerate 3 letters with the improved prompt.
6. Save the best prompt version as the final `document_generation.j2`.

Key improvements to try:
- Add a brief exemplar letter snippet showing correct NHS format
- Add explicit instructions: "Use EXACT values from patient context — do not round or fabricate"
- Add: "Include both positive AND negative findings from the consultation"
- Add: "If a discussed value differs from the record, mark with [DISCREPANCY]"

**Files created or modified:** `backend/prompts/document_generation.j2` (updated)  
**"Done" criteria:** 3 regenerated letters visually conform to NHS clinic letter format. Each letter contains FHIR-sourced values (spot-check: Mrs Thompson letter includes HbA1c 55 and eGFR 52). Letters are 300–500 words.  
**Verification method:** Manual review of 3 generated letters. Check for the presence of specific FHIR values.  
**If this fails:** Continue iterating on the prompt. If quality plateaus, document the best prompt and move on — prompt engineering has diminishing returns after 3–4 iterations.

---

### Task 17: End-to-End Backend Pipeline Wiring

**Prerequisites:** Task 16  
**Priority:** Core

**Description:**  
Connect the `/consultations/{id}/end` endpoint to the full pipeline including MedGemma 27B document generation:

1. Update `backend/orchestrator.py` — `end_consultation()` now:
   - Stage 1: Transcribe audio via MedASR → Transcript
   - Stage 2: Retrieve patient context via EHR Agent → PatientContext (may already be cached)
   - Stage 3: Generate document via MedGemma 27B → ClinicalDocument
   - Update PipelineProgress at each stage
   - Store final ClinicalDocument in Consultation object
   - Set status to `review`
2. Update `backend/api.py`:
   - `GET /consultations/{id}/document` returns the generated ClinicalDocument
   - `POST /consultations/{id}/document/sign-off` updates status to signed_off
   - `POST /consultations/{id}/document/regenerate-section` regenerates one section
3. Add latency logging: total pipeline time, time per stage.

Wire `torch.cuda.empty_cache()` between each model's inference step (see `clarke_PRD_technical_spec.md` §12, Pitfall 3).

**Files created or modified:** `backend/orchestrator.py` (major update), `backend/api.py` (add document endpoints)  
**"Done" criteria:** Complete pipeline works: `POST /consultations/start` → `POST /consultations/{id}/audio` (upload WAV) → `POST /consultations/{id}/end` → `GET /consultations/{id}/document` returns a ClinicalDocument with ≥4 sections. Total latency <60s on GPU (or <5s in mock mode).  
**Verification method:** Run the full API flow with curl commands. Check that the returned document JSON has sections with headings and content. Check latency logged in stdout.  
**If this fails:** Debug stage by stage. Check orchestrator state transitions. Ensure `torch.cuda.empty_cache()` is called between models.

---

### Task 18: Pipeline Hardening — Error Handling & Timeouts

**Prerequisites:** Task 17  
**Priority:** Core

**Description:**  
Add error handling for all failure modes defined in `clarke_PRD_technical_spec.md` §10:

1. **Pipeline timeout:** `asyncio.wait_for()` wrapper with `PIPELINE_TIMEOUT_S=120`. If exceeded, return `ErrorResponse` with `error="timeout"`.
2. **OOM recovery:** Catch `torch.cuda.OutOfMemoryError`, call `empty_cache()`, reduce `max_new_tokens` by 50%, retry once.
3. **Empty transcript handling:** If MedASR returns empty text, return `ErrorResponse` with `error="audio_error"` and message "Audio could not be transcribed."
4. **FHIR failure degradation:** If EHR Agent fails or FHIR is unreachable, continue with transcript-only document generation. Add warning to `PatientContext.retrieval_warnings`.
5. **Empty/corrupted audio:** Validate audio before MedASR. Return `ErrorResponse` for invalid files.

Test 3 error scenarios:
- Empty audio file → error response
- FHIR server unavailable → document generated from transcript only
- Oversized context (>4096 tokens) → context truncated, generation proceeds

**Files created or modified:** `backend/orchestrator.py` (add error handling), `tests/test_e2e.py` (add error scenario tests)  
**"Done" criteria:** All 3 error scenarios handled gracefully — no crashes, informative error messages returned. `pytest tests/test_e2e.py` passes including error scenario tests.  
**Verification method:** `pytest tests/test_e2e.py -v` passes. Specifically: `test_pipeline_timeout`, `test_fhir_failure_degradation`, `test_empty_audio` all pass.  
**If this fails:** Check exception handling order. Ensure `try/except` blocks don't swallow errors silently.

---

### Task 19: Phase 2 Checkpoint

**Prerequisites:** Task 18  
**Priority:** Core

**Description:**  
Run the full Phase 2 verification:

1. Full pipeline test: Upload Mrs Thompson WAV → transcript → context → letter. Letter contains HbA1c 55 and eGFR 52.
2. All 3 demo patients produce clinically coherent letters via the pipeline.
3. Pipeline latency <60s on GPU (or <5s in mock mode).
4. Error scenarios pass (empty audio, FHIR down, timeout).
5. `pytest tests/ -v` — all tests pass, 0 failures.

**Files created or modified:** None  
**"Done" criteria:** All 5 checks pass.  
**Verification method:** Run each check. Full test suite: `pytest tests/ -v`.  
**If this fails:** Fix failing tests/scenarios before proceeding to UI work.

---

## PHASE 3 — UI Build & Integration (Hours 13–16)

**Phase goal:** Functional Gradio UI connected to the backend. Complete end-to-end demo working in browser.  
**Estimated time:** 4 hours  
**Day-end checkpoint contribution:** Achieves Integration Test Point 2 (implementation.md §8).  
**Context required:** `clarke_PRD_technical_spec.md` (§9), `clarke_PRD_design_guidelines.md` (§1–§5), `clarke_PRD_userflow.md` (all sections).

---

### Task 20: Gradio Theme & CSS Setup

**Prerequisites:** Task 19  
**Priority:** Core

**Description:**  
Create the visual foundation for Clarke's UI.

20a. **`frontend/theme.py`** — Create a Gradio theme using Clarke's colour tokens from `clarke_PRD_design_guidelines.md` §1:
- Primary colour: `#1E3A5F` (clarke-blue)
- Secondary colour: `#D4A035` (clarke-gold)
- Background: `#FAFBFD` (clarke-bg-primary)
- Text: `#1A1A2E` (clarke-text-primary)
- Use `gr.themes.Base()` as starting point, override colours.

20b. **`frontend/assets/style.css`** — Custom CSS with:
- All CSS custom properties from design_guidelines §1 (--clarke-blue, --clarke-gold, etc.)
- Hero gradient background (§1 gradient spec)
- Typography: Inter font import, type scale (§2)
- Card styling: border-radius 12px, shadow, hover effects (§3, §4)
- Paper container for document display: max-width 720px, centered, inset shadow (§4.6 from userflow)
- Recording pulse animation keyframes (§4.5 from design_guidelines)
- Skeleton loader animation (shimmer effect)

20c. **`frontend/assets/clarke_logo.svg`** — Create a simple SVG logo (shield/C shape in clarke-blue and clarke-gold).

**Files created or modified:** `frontend/theme.py`, `frontend/assets/style.css`, `frontend/assets/clarke_logo.svg`  
**"Done" criteria:** Theme and CSS files exist with all specified tokens. A minimal Gradio app using the theme renders with Clarke colours.  
**Verification method:** `python -c "import gradio as gr; from frontend.theme import clarke_theme; demo = gr.Blocks(theme=clarke_theme, css='frontend/assets/style.css'); demo.launch(prevent_thread_lock=True)"` launches without error and shows Clarke styling.  
**If this fails:** Check CSS syntax. Ensure theme object is a valid `gr.Theme`.

---

### Task 21: Gradio UI — Core Layout & Dashboard (S1)

**Prerequisites:** Task 20  
**Priority:** Core

**Description:**  
Build the main UI structure and the Dashboard screen (S1) in `frontend/ui.py`.

The `build_ui()` function returns a `gr.Blocks` layout with:

1. **Top bar:** Clarke logo, "Clarke" text, status indicator.
2. **Main content area** — uses `gr.Column` with visibility toggling to switch between screens (S1–S6).
3. **S1 — Dashboard:**
   - Clinic header: "Dr. Sarah Chen — Diabetes & Endocrinology — 13 February 2026"
   - Hero gradient background (via CSS class)
   - Patient card list: 5 cards, each showing name, age/sex, appointment time, one-line summary
   - Cards are `gr.Button` styled as cards (or `gr.HTML` with click events)
   - Clicking a card triggers patient selection → transition to S2

4. **`frontend/state.py`** — Implement state management:
   - `gr.State` holds current screen name, consultation object, selected patient
   - Screen visibility functions: `show_screen(screen_name)` returns visibility updates for all screen containers

5. **`frontend/components.py`** — Reusable component builders:
   - `build_patient_card(patient: dict) -> gr.HTML` — renders a styled patient card
   - `build_status_badge(status: str) -> gr.HTML` — renders status badge with appropriate colour

Also create `app.py` — the entry point that mounts Gradio + FastAPI together (per `clarke_PRD_technical_spec.md` §9a):
```python
demo = build_ui()
demo = gr.mount_gradio_app(fast_api, demo, path="/")
```

**Files created or modified:** `frontend/ui.py`, `frontend/state.py`, `frontend/components.py`, `app.py`  
**"Done" criteria:** `python app.py` launches at localhost:7860. Dashboard shows 5 patient cards with correct names and details. Clicking a card triggers a visible event (even if transition is not yet complete).  
**Verification method:** Launch app, open browser to localhost:7860. Visual check: 5 patient cards are visible. `data/clinic_list.json` data is rendered correctly.  
**If this fails:** Check Gradio Blocks layout. Ensure `clinic_list.json` is loaded correctly. Verify CSS is applied.

---

### Task 22: Gradio UI — Patient Context & Recording (S2, S3)

**Prerequisites:** Task 21  
**Priority:** Core

**Description:**  
Build screens S2 (Patient Context) and S3 (Live Consultation).

**S2 — Patient Context:**
- Left panel: Patient context display with sections: Demographics, Problem List, Medications, Allergies (highlighted with ⚠), Recent Labs (with trend arrows ↑↓), Recent Imaging, Clinical Flags
- Centre panel: Empty document area with CTA text "Start Consultation" and "Back to Dashboard" button
- On patient selection: call EHR Agent (or mock) to get PatientContext, populate left panel
- Skeleton loaders while context loads (CSS shimmer animation)

**S3 — Live Consultation:**
- Recording indicator (gold pulsing circle, using CSS animation from Task 20)
- Timer showing elapsed time (MM:SS format, updated via `gr.Timer`)
- Audio capture: use `gr.Audio(sources=["microphone"], streaming=False)` as the pragmatic Gradio approach (capture complete audio, not streaming chunks). If Gradio streaming works, use it; otherwise, capture entire audio on "End Consultation".
- "End Consultation" button (primary style)
- Expandable transcript panel (initially minimised, shows transcript after processing)
- Patient context remains visible on the left (collapsed summary)

Wire the screen transitions:
- S1 → S2: Patient card click → load context → show S2
- S2 → S3: "Start Consultation" click → show S3, start audio capture
- S2 → S1: "Back to Dashboard" → show S1

**Files created or modified:** `frontend/ui.py` (add S2, S3)  
**"Done" criteria:** Select a patient on S1 → S2 loads with patient context (from mock/API). Click "Start Consultation" → S3 shows with recording indicator and audio capture widget. "Back to Dashboard" returns to S1.  
**Verification method:** Visual check through the flow: S1 → click patient → S2 shows context → click Start → S3 shows recording UI.  
**If this fails:** Debug Gradio event handlers. Ensure `gr.State` updates correctly. If audio capture fails, use `gr.Audio(sources=["upload"])` as fallback.

---

### Task 23: Gradio UI — Processing, Review & Sign-off (S4, S5, S6)

**Prerequisites:** Task 22  
**Priority:** Core

**Description:**  
Build screens S4 (Processing), S5 (Document Review), and S6 (Signed Off).

**S4 — Processing:**
- Three-stage progress indicator showing: "Finalising transcript…" → "Synthesising patient context…" → "Generating clinical letter…"
- Use `gr.Timer(every=1)` to poll pipeline progress and update the stage display
- Simple progress bar (3 segments) with the active segment highlighted in clarke-blue
- Elapsed timer
- "Cancel" button (secondary, destructive)

**S5 — Document Review:**
- Centre panel: Generated NHS clinic letter rendered in a paper container (max-width 720px, white, subtle shadow)
- Letter displayed section by section using `gr.Textbox(interactive=True)` for each section (allowing inline editing)
- FHIR-sourced values: wrap in monospace spans via `gr.HTML` or `gr.Markdown`
- Status badge: "Ready for Review" (amber)
- "Sign Off & Export" button (primary)
- "Regenerate Entire Letter" button (secondary)
- Left panel: collapsed patient context summary

**S6 — Signed Off:**
- Read-only letter display
- Status badge: "Signed Off" (green ✓)
- Export buttons: "Copy to Clipboard", "Download as Text"
- "Next Patient" button → returns to S1 with next patient highlighted

Wire transitions:
- S3 → S4: "End Consultation" → upload audio → trigger pipeline → show S4
- S4 → S5: Pipeline complete → show S5 with generated document
- S5 → S6: "Sign Off" → mark signed → show S6
- S6 → S1: "Next Patient" → reset state → show S1

**Files created or modified:** `frontend/ui.py` (add S4, S5, S6)  
**"Done" criteria:** All 6 screens exist and are navigable. The complete flow S1→S2→S3→S4→S5→S6→S1 works with mock data.  
**Verification method:** Visual walk-through of entire flow using mock mode. Each screen renders correct content.  
**If this fails:** Focus on getting the flow working with minimal styling. Polish comes later. If `gr.Timer` polling is problematic, use a simpler approach (single blocking call with loading indicator).

---

### Task 24: UI ↔ Backend Data Binding

**Prerequisites:** Task 23  
**Priority:** Core

**Description:**  
Connect all UI interactions to the real backend:

1. **Patient selection (S1 → S2):** Card click calls `POST /patients/{id}/context` → context panel populates with real FHIR data.
2. **Start Consultation (S2 → S3):** Calls `POST /consultations/start` with patient_id → stores consultation_id in `gr.State`.
3. **Audio capture (S3):** Gradio audio component captures audio. On "End Consultation", uploads audio to `POST /consultations/{id}/audio` then calls `POST /consultations/{id}/end`.
4. **Processing (S4):** Polls `GET /consultations/{id}/progress` every second. Updates stage labels. When stage = "complete", fetches document from `GET /consultations/{id}/document` and transitions to S5.
5. **Document display (S5):** Renders `ClinicalDocument` sections as editable textboxes. Each section shows heading + content.
6. **Sign Off (S5 → S6):** Calls `POST /consultations/{id}/document/sign-off` with any edited sections.
7. **Next Patient (S6 → S1):** Resets `gr.State`, returns to dashboard.

Ensure the backend calls work correctly with both mock mode and real model mode.

**Files created or modified:** `frontend/ui.py` (major update — event binding), `frontend/state.py` (update)  
**"Done" criteria:** In mock mode: the complete flow works end-to-end in the browser. Select patient → context loads → start consultation → provide audio → end → processing animation → letter appears → edit → sign off → export → next patient.  
**Verification method:** Full manual walkthrough in browser at localhost:7860. Each step produces the expected result.  
**If this fails:** Debug one step at a time. Check browser console for JavaScript errors. Check server logs for API errors. The most likely failure points are: audio upload format, progress polling timing, and state management.

---

### Task 25: End-to-End Demo Scenario Testing (3 patients)

**Prerequisites:** Task 24  
**Priority:** Core

**Description:**  
Test all 3 demo scenarios completely:

1. **Mrs Thompson (pt-001):** Upload `mrs_thompson.wav` → transcript mentions diabetes topics → context shows HbA1c 55, eGFR 52, Penicillin allergy → letter includes these values → edit one line → sign off.
2. **Mr Okafor (pt-002):** Upload `mr_okafor.wav` → transcript mentions chest pain → context shows normal coronaries → letter discusses angiogram results → sign off.
3. **Ms Patel (pt-003):** Upload `ms_patel.wav` → transcript mentions asthma → context shows peak flow 320 → letter recommends preventer inhaler → sign off.

For each scenario:
- Verify correct transcription (transcript text is clinically relevant)
- Verify correct context (FHIR data matches patient)
- Verify letter quality (contains both transcript content AND FHIR values)
- Verify editing works (change one paragraph)
- Verify sign-off works

Fix any bugs discovered during testing.

**Files created or modified:** Bug fixes in various files  
**"Done" criteria:** All 3 scenarios complete without crashes. Generated letters are clinically appropriate for each patient.  
**Verification method:** Manual run-through of each scenario in browser. Screenshot or note the key assertion for each (e.g., "Thompson letter contains HbA1c 55").  
**If this fails:** Fix bugs for each specific scenario. Most common issues: wrong patient context loaded, transcript doesn't match audio file, document parsing fails for certain prompt outputs.

---

### Task 26: Phase 3 Checkpoint — Integration Test Point 2

**Prerequisites:** Task 25  
**Priority:** Core

**Description:**  
This is **Integration Test Point 2** from `clarke_PRD_implementation.md` §8.

**Full demo dry-run:** Perform the Mrs Thompson scenario exactly as it would appear in the competition video:

1. Open Clarke in browser
2. Select Mrs Thompson from patient list
3. Verify context panel populates with correct data
4. Click "Start Consultation", upload pre-recorded audio
5. Click "End Consultation"
6. Verify draft letter appears within 60 seconds (or <5s mock mode)
7. Verify letter contains FHIR-sourced lab values
8. Edit one line, click "Sign Off"
9. Verify status transitions to green

Also: Run `pytest tests/ -v` — all tests still pass (no regressions).

**📌 DAY 2 DECISION POINT (from masterplan §12):** At this point, assess the must-have list:
1. ✅ Working MedASR transcription
2. ✅ Working EHR Agent context retrieval
3. ✅ Working document generation
4. ✅ End-to-end orchestration
5. ✅ Functional Gradio UI
6. ✅ 3 demo scenarios tested

**If ≥2 must-haves are incomplete:** Cancel ALL nice-to-haves (Tasks 27–32). Day 3 is entirely: fix remaining must-haves → deploy.

**Files created or modified:** None  
**"Done" criteria:** Demo dry-run completes smoothly. `pytest tests/` passes. All must-haves are checked.  
**Verification method:** Manual demo run + test suite.  
**If this fails:** This is the last chance to fix critical issues. Prioritise by: pipeline > UI > polish.

---

## PHASE 4 — Fine-tuning, Evaluation & Polish (Hours 17–21)

**Phase goal:** LoRA fine-tuning (if feasible), quantitative evaluations, UI polish, demo preparation.  
**Estimated time:** 5 hours  
**Day-end checkpoint contribution:** Nice-to-haves from masterplan §12.  
**Context required:** `clarke_PRD_technical_spec.md` (§6c fine-tuning params, §11), `clarke_PRD_design_guidelines.md` (full), `clarke_PRD_implementation.md` (§3 Phase 4).

**All tasks in this phase are Priority: Polish** — they improve the submission but are not required for a functional demo. If behind schedule, skip directly to Phase 5 (Task 34).

---

### Task 27: Synthetic Training Data Generation

**Prerequisites:** Task 26  
**Priority:** Polish

**Description:**  
Generate 250 training triplets (transcript, FHIR context JSON, reference NHS letter) for fine-tuning MedGemma 27B.

Implement `finetuning/generate_training_data.py`:
1. Use Claude API (or another LLM API) to generate diverse clinical scenarios.
2. Each triplet contains:
   - `transcript`: A simulated clinician-patient consultation transcript (~200 words)
   - `context`: A PatientContext JSON with realistic FHIR-sourced data
   - `reference_letter`: A gold-standard NHS clinic letter
3. Clinical scenarios distributed across specialties (per `clarke_PRD_technical_spec.md` §8a).
4. Output format: JSONL with one triplet per line.
5. Split: 200 train → `data/training/train.jsonl`, 50 test → `data/training/test.jsonl`.
6. Manually review 20 samples for quality: clinically plausible, correctly formatted, no fabricated data conflicts.

**Files created or modified:** `finetuning/generate_training_data.py`, `data/training/train.jsonl`, `data/training/test.jsonl`  
**"Done" criteria:** `train.jsonl` has 200 lines, `test.jsonl` has 50 lines. Each line is valid JSON with keys: transcript, context, reference_letter. 20 reviewed samples pass quality check.  
**Verification method:** `wc -l data/training/train.jsonl` = 200. `python -c "import json; [json.loads(l) for l in open('data/training/train.jsonl')]"` succeeds.  
**If this fails:** If API generation fails, reduce to 100 training samples. If quality is poor (>20% fail review), revise generation prompt and regenerate.

---

### Task 28: LoRA Fine-tuning MedGemma 27B

**Prerequisites:** Task 27  
**Priority:** Polish

**Description:**  
Implement and run QLoRA fine-tuning in `finetuning/train_lora.py`.

**Configuration (from `clarke_PRD_technical_spec.md` §3a and `clarke_PRD_implementation.md` §3 Hour 18):**
- Base model: `google/medgemma-27b-text-it` in 4-bit NF4
- LoRA config: `rank=16, alpha=32, dropout=0.05`, target modules: attention + MLP layers
- Training: `epochs=3, batch_size=2, gradient_accumulation_steps=8, learning_rate=2e-4`
- `max_seq_length=4096`
- Trainer: `trl.SFTTrainer`
- Tracking: wandb (optional)

Steps:
1. **Unload MedASR and MedGemma 4B** from GPU before training to free VRAM.
2. Load base model in 4-bit, apply LoRA configuration.
3. Load training data from `data/training/train.jsonl`.
4. Format each sample as a prompt-completion pair using the document_generation.j2 template.
5. Train. Monitor loss.
6. Save LoRA adapter to `finetuning/adapter/`.
7. **Reload MedASR and MedGemma 4B** after training.

**Files created or modified:** `finetuning/train_lora.py`, `finetuning/adapter/` (saved adapter files)  
**"Done" criteria:** Training completes without OOM. Final training loss < initial loss. Adapter saved, <500MB.  
**Verification method:** Check training logs for loss curve. `ls -lh finetuning/adapter/` shows adapter files.  
**If this fails:** **⚠️ FALLBACK (from implementation.md §3):** If training fails after 2 attempts:
1. Reduce LoRA rank from 16 to 8.
2. Reduce max_seq_length from 4096 to 2048.
3. Reduce training set from 200 to 100.
4. If still fails after these reductions: **abandon fine-tuning entirely**. Use base MedGemma 27B with the optimised prompt from Task 16. Document fine-tuning as "production roadmap" in the writeup. Skip Task 35 (LoRA publication). Redirect remaining time to Tasks 29–32 (evaluation and polish).

---

### Task 29: MedASR Evaluation (WER)

**Prerequisites:** Task 26  
**Priority:** Polish

**Description:**  
Implement `evaluation/eval_medasr.py`:
1. Compute Word Error Rate (WER) for MedASR on the 3 demo audio clips using `jiwer`.
2. Ground-truth transcripts: `data/demo/*_transcript.txt`.
3. Optionally compare to Whisper large-v3 on the same clips.
4. Output: WER per clip + average WER. Save results to `evaluation_report.md`.

**Files created or modified:** `evaluation/eval_medasr.py`, `evaluation_report.md` (create/append)  
**"Done" criteria:** WER computed for all 3 clips. Results appended to evaluation_report.md.  
**Verification method:** `cat evaluation_report.md | grep "MedASR WER"` shows results.  
**If this fails:** If jiwer fails, compute WER manually. If MedASR WER is >15% on demo clips, note this and consider switching to dictation-style audio (see `clarke_PRD_implementation.md` §7, Fallback Path #4).

---

### Task 30: EHR Agent Evaluation (Fact Recall)

**Prerequisites:** Task 26  
**Priority:** Polish

**Description:**  
Implement `evaluation/eval_ehr_agent.py`:
1. For each of 5 demo patients, compare EHR Agent output (`PatientContext`) against gold-standard context.
2. Create gold standards in `evaluation/gold_standards/` — manually verified correct context for each demo patient.
3. Metrics: Fact recall (what % of gold facts appear in output), Precision (what % of output facts are correct), Hallucination rate (what % of output facts are not in gold standard or FHIR data).
4. Target from masterplan §11: recall >85%, precision >90%, hallucination <10%.
5. Append results to `evaluation_report.md`.

**Files created or modified:** `evaluation/eval_ehr_agent.py`, `evaluation/gold_standards/pt-001.json` through `pt-005.json`, `evaluation_report.md` (append)  
**"Done" criteria:** Metrics computed for 5 patients. Results in evaluation_report.md.  
**Verification method:** `cat evaluation_report.md | grep "Fact Recall"` shows results.  
**If this fails:** If metrics are below target, note the gaps and adjust EHR agent prompts if time permits.

---

### Task 31: Document Generation Evaluation (BLEU/ROUGE-L)

**Prerequisites:** Task 28 (if fine-tuned) or Task 26 (if using base model)  
**Priority:** Polish

**Description:**  
Implement `evaluation/eval_doc_gen.py`:
1. Generate letters for 50 test triplets from `data/training/test.jsonl`.
2. Compute BLEU (sacrebleu) and ROUGE-L (rouge_score) against reference letters.
3. If fine-tuned model is available, compare fine-tuned vs baseline (3 letters from Task 15).
4. Manual review of 10 test letters for NHS format compliance and clinical accuracy.
5. Append results to `evaluation_report.md`.

**Files created or modified:** `evaluation/eval_doc_gen.py`, `evaluation_report.md` (append)  
**"Done" criteria:** BLEU and ROUGE-L computed. If fine-tuned: fine-tuned scores > baseline scores. Results in evaluation_report.md.  
**Verification method:** `cat evaluation_report.md | grep "BLEU\|ROUGE"` shows results.  
**If this fails:** If evaluation takes too long, reduce test set to 20 triplets. Focus on getting numbers that demonstrate improvement.

---

### Task 32: UI Visual Polish

**Prerequisites:** Task 26  
**Priority:** Polish

**Description:**  
Apply visual polish from `clarke_PRD_design_guidelines.md`:

1. **Hero gradient** (§1): Apply the warm-to-cool gradient behind the dashboard header.
2. **Card styling** (§3–§4): Rounded corners (12px), subtle shadow, hover elevation on patient cards.
3. **Recording indicator** (§4.5 from design_guidelines): Gold pulsing circle with ring animation.
4. **Loading states** (§4.8): Skeleton loaders with shimmer animation during context retrieval and processing.
5. **Document reveal** (§5): Subtle scale animation (0.97→1.0) when the letter first appears.
6. **Typography tightening**: Ensure Inter font loads, correct type scale is applied.
7. **Status badges**: Correct colours for each state (amber for review, green for signed off).
8. **Progress bar**: Three-segment bar with active segment glow.

Focus on the elements visible in the demo video — they carry the most judging weight.

**Files created or modified:** `frontend/assets/style.css` (major update), `frontend/ui.py` (add CSS classes), `frontend/components.py` (update)  
**"Done" criteria:** UI looks professional and polished. Hero gradient visible on dashboard. Patient cards have hover effects. Recording shows gold pulse. Document appears with subtle animation. Status badges use correct colours.  
**Verification method:** Visual inspection in browser at 1920×1080. All specified visual elements are present.  
**If this fails:** Prioritise: (1) hero gradient, (2) card styling, (3) recording pulse, (4) status badges. Skip animations if they cause issues.

---

### Task 33: Phase 4 Checkpoint

**Prerequisites:** Task 26 + any completed Tasks 27–32  
**Priority:** Core

**Description:**  
Assess what was completed in Phase 4 and ensure core functionality still works:

1. `pytest tests/ -v` — all tests pass (no regressions from polish work).
2. Full demo dry-run of Mrs Thompson scenario — still works end-to-end.
3. Inventory completed nice-to-haves:
   - [ ] LoRA fine-tuning completed?
   - [ ] LoRA adapter saved?
   - [ ] WER evaluation completed?
   - [ ] EHR Agent evaluation completed?
   - [ ] BLEU/ROUGE-L evaluation completed?
   - [ ] UI visually polished?
   - [ ] evaluation_report.md populated?

This inventory informs what to include in the writeup and video.

**Files created or modified:** None  
**"Done" criteria:** Tests pass. Demo works. Inventory documented.  
**Verification method:** Test suite + demo run + checklist.  
**If this fails:** Fix any regressions before deployment.

---

## PHASE 5 — Deployment & Submission Prep (Hours 22–24)

**Phase goal:** Public HF Space live, public GitHub repo, all submission artefacts ready.  
**Estimated time:** 3 hours  
**Day-end checkpoint contribution:** Achieves Day 3 checkpoint — competition-ready (minus video/writeup, scheduled for buffer week).  
**Context required:** `clarke_PRD_technical_spec.md` (§3b), `clarke_PRD_implementation.md` (§3 Phase 5, §9).

---

### Task 34: HF Space Deployment

**Prerequisites:** Task 33  
**Priority:** Core

**Description:**  
Deploy Clarke to a public Hugging Face Space:

1. Ensure `Dockerfile` is correct and complete (from Task 2).
2. Ensure `requirements.txt` includes all dependencies.
3. Create HF Space with hardware: `a100-large` (A100 40GB GPU).
4. Set `README.md` YAML frontmatter for HF Spaces metadata:
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
5. Set environment variables as HF Space secrets: `HF_TOKEN`, `USE_MOCK_FHIR=true`.
6. Push code to HF Space repo.
7. Wait for build + startup.
8. Test: access the public URL from an incognito browser, run one demo scenario end-to-end.

**Deployment decision:** If A100 quota is unavailable or too expensive during development, deploy with `USE_MOCK_FHIR=true` and model mocks, then upgrade to GPU hardware for the final submission. The mock demo still demonstrates the full UI flow.

**Files created or modified:** `README.md` (update frontmatter), HF Space configuration  
**"Done" criteria:** Public HF Space URL is accessible from incognito browser. Demo scenario (select patient → context loads → upload audio → letter generates → sign off) completes without errors.  
**Verification method:** Open HF Space URL in incognito browser on a different device. Run Mrs Thompson scenario.  
**If this fails:** Check HF Space build logs for errors. Most common issues: Docker build fails (missing system packages), model download fails (HF_TOKEN not set), CUDA not available (wrong hardware tier). If GPU deployment fails entirely: deploy with mock models as a UI demo, note in writeup that full GPU demo is available locally.

---

### Task 35: HF Hub LoRA Adapter Publication

**Prerequisites:** Tasks 28, 34  
**Priority:** Polish

**Description:**  
If LoRA fine-tuning was completed (Task 28), publish the adapter on HF Hub:

1. Create a new HF Hub model repository: `{username}/clarke-medgemma-27b-nhs-letter-lora`
2. Upload the LoRA adapter files from `finetuning/adapter/`.
3. Create a model card (README.md) in the repo:
   - Description: "LoRA adapter for NHS clinic letter generation, fine-tuned on MedGemma 27B"
   - Base model: `google/medgemma-27b-text-it`
   - Training details: hyperparameters, dataset size, training loss
   - Usage example: loading the adapter with `peft`
   - Licence: follow HAI-DEF terms
4. Verify: the model repo page shows correct metadata and files.

**Files created or modified:** HF Hub model repository files  
**"Done" criteria:** Public HF Hub model repo exists, contains adapter files, has model card tracing to `google/medgemma-27b-text-it`.  
**Verification method:** Visit the HF Hub model page in a browser. Verify adapter files are listed and model card is readable.  
**If this fails:** If upload fails, try manual upload via the HF Hub web interface. If fine-tuning was not completed, skip this task entirely.

---

### Task 36: GitHub Repo & README

**Prerequisites:** Task 34  
**Priority:** Core

**Description:**  
Prepare the public GitHub repository:

1. **Code cleanup:** Ensure all `.py` files have module-level docstrings. Remove any debug print statements. Verify all imports are used.
2. **`README.md`** — Write a comprehensive README:
   - Project title and one-line description
   - Architecture diagram (ASCII art or embedded image): show the three-model pipeline with arrows
   - Features list
   - Quick start: installation, environment setup, local run
   - Evaluation results (from `evaluation_report.md`, if completed)
   - Model information: list all 3 HAI-DEF models with HF links
   - Links: HF Space demo, HF LoRA adapter (if published)
   - Licence: Apache 2.0 for code, HAI-DEF terms for models
   - Acknowledgements: MedGemma Impact Challenge, Synthea, HAPI FHIR
3. **Repository setup:**
   - `.gitignore` — Python standard + `__pycache__`, `.env`, `logs/`, model weights, `*.wav` (keep demo wavs via LFS or small files)
   - Push to public GitHub repository
   - Verify: README renders correctly on GitHub

**Files created or modified:** `README.md` (comprehensive update), `.gitignore`, all `.py` files (docstrings), GitHub repo  
**"Done" criteria:** Public GitHub repo has clean code, comprehensive README with architecture diagram, all `.py` files have docstrings, licence file present.  
**Verification method:** Visit GitHub repo URL. README renders correctly. `grep -rL '"""' backend/ frontend/ --include="*.py"` returns no files (all have docstrings).  
**If this fails:** Focus on README quality first — judges will read it. Docstrings can be minimal if time is short.

---

### Task 37: Final Smoke Test & Submission Checklist

**Prerequisites:** Task 36  
**Priority:** Core

**Description:**  
Run the complete final verification:

1. **HF Space test:** Open live HF Space from incognito browser on a different device. Run all 3 demo scenarios. Verify each produces a clinically appropriate letter.
2. **GitHub repo test:** Clone the public repo into a fresh environment. Verify `README.md` has all required sections. Verify all Python files have docstrings.
3. **Links check:** All links in README are valid (HF Space, GitHub, HF model repo if applicable).
4. **Create `submission_checklist.md`:**

```markdown
# Clarke — Submission Checklist

## Ready Now (End of 24-Hour Build)
- [ ] Public HF Space: [URL] — accessible, runs 3 demo scenarios
- [ ] Public GitHub repo: [URL] — clean code, README, licence
- [ ] Public LoRA adapter: [URL] (if trained) — traces to google/medgemma-27b-text-it
- [ ] evaluation_report.md — metrics computed (if completed)

## Buffer Week (Mon 16 – Sun 22 Feb)
- [ ] 3-page writeup (Mon 16 Feb)
- [ ] 3-minute video (Tue 17 – Sat 21 Feb)
- [ ] Final Kaggle submission (Sun 22 Feb)
  - [ ] Writeup submitted via Kaggle Writeups tab
  - [ ] Agentic Workflow Prize selected
  - [ ] All links included: video, GitHub, HF Space, HF model
```

**Files created or modified:** `submission_checklist.md`  
**"Done" criteria:** All "Ready Now" items are checked. HF Space demo works from external device. GitHub repo is public with complete README.  
**Verification method:** Walk through each checklist item. Test each link from incognito browser.  
**If this fails:** Fix the specific failing item. Prioritise: HF Space working > GitHub repo > LoRA adapter.

---

### Task 38: Phase 5 Checkpoint — Final

**Prerequisites:** Task 37  
**Priority:** Core

**Description:**  
Final checkpoint. Verify all Day 3 end-of-build criteria from `clarke_PRD_implementation.md` §5:

1. ✅ Public HF Space is live and accessible from any browser.
2. ✅ Public GitHub repo with clean code, README with architecture diagram, and docstrings.
3. ✅ At least 3 demo scenarios work flawlessly on the live HF Space.
4. ✅ Submission checklist confirms all competition requirements are met (except video and writeup).

**Nice-to-haves completed (record for writeup/video planning):**
- LoRA adapter trained and published? Y/N
- WER comparison table? Y/N
- EHR Agent metrics? Y/N
- BLEU/ROUGE-L evaluation? Y/N
- evaluation_report.md populated? Y/N
- UI visually polished? Y/N

**Files created or modified:** None  
**"Done" criteria:** All 4 Day 3 criteria are met. Inventory of completed nice-to-haves is documented.  
**Verification method:** Go through each criterion. If all pass: the 24-hour build is complete. Proceed to buffer week for writeup and video.  
**If this fails:** The buffer week (Mon 16 – Sun 22 Feb) absorbs remaining work. Prioritise by competition impact: working demo > evaluation metrics > fine-tuning > polish.

---

## Appendix A: Fallback Decision Points Summary

| Task | Risk | Trigger | Fallback | Impact |
|------|------|---------|----------|--------|
| T11 | MedGemma 4B instruction-following | Fails after 2h of prompt engineering | Deterministic FHIR + summarisation only | Narrative slightly weaker. No downstream changes. |
| T15 | MedGemma 27B won't load | OOM on A100 at 4-bit | Try Ollama GGUF → then 4B for generation | T16–T17 adapt. Quality drops. Pipeline intact. |
| T28 | LoRA training fails | OOM, loss diverges, >2h | Skip fine-tuning. Use base model + prompt engineering. | Skip T35. Redirect time to T29–T32. |
| T29 | MedASR WER >15% | Demo clips produce poor transcripts | Switch to dictation-style audio | Swap audio files. Rest unchanged. |
| T34 | HF Space deployment fails | Build errors, GPU unavailable | Deploy with mock models. Demo UI flow only. | Note GPU demo in writeup as local-only. |

## Appendix B: PRD Cross-Reference per Phase

| Phase | Required PRD Files in Context |
|-------|------------------------------|
| 0 | `clarke_PRD_technical_spec.md` (§1–§3, §7–§8) |
| 1 | `clarke_PRD_technical_spec.md` (§6a–§6b, §7, §9), `clarke_PRD_implementation.md` (Phase 1) |
| 2 | `clarke_PRD_technical_spec.md` (§6c, §10), `clarke_PRD_implementation.md` (Phase 2) |
| 3 | `clarke_PRD_technical_spec.md` (§9), `clarke_PRD_design_guidelines.md` (§1–§5), `clarke_PRD_userflow.md` |
| 4 | `clarke_PRD_technical_spec.md` (§6c fine-tuning, §11), `clarke_PRD_design_guidelines.md`, `clarke_PRD_implementation.md` (Phase 4) |
| 5 | `clarke_PRD_technical_spec.md` (§3b), `clarke_PRD_implementation.md` (§3 Phase 5, §9) |

---

*This document is the construction schedule that turns the Clarke blueprint into a working product. Every task traces to a specific section of clarke_PRD_technical_spec.md (architecture), clarke_PRD_implementation.md (build sequence), clarke_PRD_userflow.md (screens), or clarke_PRD_design_guidelines.md (visual specification). Codex executes one task at a time, verifies, and moves on. The user confirms progress at each phase checkpoint.*
