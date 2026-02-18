# Clarke Evaluation Report

## 1. MedASR: Word Error Rate Evaluation

### 1.1 Motivation

MedASR sits at the entry point of Clarke's three-agent pipeline. Every downstream output — EHR retrieval queries, clinical letter content, medication lists — depends on the fidelity of this initial transcription. A substitution of "gliclazide" → "gliplizide" is recoverable; a hallucinated dosage is not. Quantifying transcription accuracy is therefore not optional — it is a prerequisite for trusting any output Clarke produces.

We selected Word Error Rate (WER) as our primary metric because it is the established standard in speech recognition research, it operates at the word level (matching the granularity of clinical meaning), and it permits direct comparison with published ASR benchmarks. WER is defined as:

> WER = (Substitutions + Insertions + Deletions) / Reference Word Count

A WER of 0% indicates perfect transcription. Lower is better.

### 1.2 Model Specification

| Parameter | Value |
|-----------|-------|
| Model | `google/medasr` (HAI-DEF collection) |
| Architecture | Connectionist Temporal Classification (CTC) |
| Model class | `AutoModelForCTC` (HuggingFace Transformers) |
| Processor | `AutoProcessor.from_pretrained("google/medasr")` |
| Input | 16 kHz mono PCM WAV |
| Decoding | Greedy argmax → consecutive-duplicate collapse → CTC blank removal |
| Inference hardware | NVIDIA A100 80 GB (HuggingFace Spaces) |

CTC models emit one token per audio frame, including a blank symbol (ε) representing "no new character at this timestep." Standard CTC decoding collapses adjacent duplicates and strips blanks to produce the final transcript. Clarke implements this explicitly: after argmax over logits, we deduplicate consecutive token IDs, remove the blank token (ID 0), and decode the remaining sequence via the processor's `batch_decode`. This approach is deterministic and adds negligible latency (<5 ms on A100).

### 1.3 Evaluation Methodology

**Test set construction.** We authored three ground-truth transcripts, each representing a complete NHS outpatient consultation with realistic clinical content: drug names, dosages, lab values, examination findings, and management plans. Audio was synthesised using macOS text-to-speech (voice: Daniel, speaking rate: 160 WPM) and converted to 16 kHz mono PCM WAV via FFmpeg.

| Clip | Clinical Scenario | Duration | Reference Words |
|------|-------------------|----------|----------------|
| Mrs Thompson | T2DM review — rising HbA1c, gliclazide dose increase, renal monitoring | 69.7 s | 214 |
| Mr Okafor | Chest pain follow-up — normal angiogram, CV risk management, BP review | 79.9 s | 194 |
| Ms Patel | Asthma review — suboptimal control, inhaler technique, beclomethasone initiation | 73.1 s | 236 |
| **Total** | | **222.7 s** | **644** |

**Why TTS rather than real clinical audio?** Two reasons. First, ground-truth alignment: TTS guarantees an exact, unambiguous reference transcript with zero human transcription error, eliminating a confounding variable. Second, reproducibility: any evaluator can regenerate identical audio from the published transcripts and replicate our results exactly. We acknowledge this is a controlled-conditions baseline and discuss real-world implications in §1.7.

**Evaluation tool.** WER was computed using `jiwer` 3.x, which implements minimum edit distance alignment between reference and hypothesis word sequences.

**Pipeline.** Each audio clip was submitted to the live Clarke deployment on HuggingFace Spaces (A100 GPU). The full production pipeline executed: audio preprocessing → MedASR inference → CTC decoding → transcript output. No post-hoc corrections or filtering were applied. The raw MedASR output was compared directly against the ground-truth transcript.

### 1.4 Results

| Clip | Ref. Words | Hyp. Words | WER |
|------|-----------|-----------|-----|
| Mrs Thompson (T2DM) | 214 | 212 | 10.75% |
| Mr Okafor (Chest pain) | 194 | 193 | 10.82% |
| Ms Patel (Asthma) | 236 | 230 | 12.29% |
| **Overall (weighted)** | **644** | **635** | **11.34%** |

Performance was consistent across all three clips (range: 10.75–12.29%), suggesting stable behaviour across different clinical domains and vocabulary distributions.

### 1.5 Error Taxonomy

We categorised all errors across the three transcripts into four types, ordered by clinical significance.

**Category 1 — Patient names (high frequency, low clinical risk)**

| Reference | Hypothesis |
|-----------|-----------|
| Thompson | Tomson |
| Mr Okafor | misterographer |
| Ms Patel | misptel |

Proper nouns are inherently difficult for CTC models trained on medical corpora, where names are rare and lack predictive context. In Clarke's pipeline, patient identity is resolved from the FHIR record, not the transcript, so name errors do not propagate to the final document.

**Category 2 — Medical terminology (low frequency, variable clinical risk)**

| Reference | Hypothesis | Risk |
|-----------|-----------|------|
| gliclazide | gliplizide | Low — phonetically similar, same drug class |
| eGFR | regar | Moderate — clinical abbreviation lost |
| preventer | Proventil / Pventil | Moderate — generic term replaced with brand name |
| thirst | thst | Low — inferable from clinical context |

Most clinical terms transcribed correctly: metformin, aspirin, atorvastatin, salbutamol, beclomethasone, troponin, angiogram, HbA1c, peak flow. Errors concentrated on less common terms and abbreviations.

**Category 3 — Units and values (low frequency, low risk)**

Numerical values were almost universally preserved: 75 mg, 40 mg, 80 mg, 200 mcg, 320 L/min, 52, 48. One unit error occurred: "55 millimoles per mole" → "55 mm/mL." Dosage numbers themselves were correct in all cases.

**Category 4 — Minor word-level errors (low frequency, negligible risk)**

Occasional substitutions on non-clinical words (e.g., "properly" → "proprily") that do not alter clinical meaning.

### 1.6 Pipeline-Level Error Mitigation

An 11.34% WER in a standalone transcription system would require careful review. In Clarke's multi-agent architecture, three downstream mechanisms compensate for transcription errors — a key advantage of the agentic design over single-model approaches:

**Agent 2 — EHR cross-referencing (MedGemma 4B).** The EHR retrieval agent independently queries the FHIR electronic health record for structured data: active conditions, current medications with dosages, lab results with dates and values. This data is authoritative and does not depend on transcription accuracy. When MedASR produces "gliplizide," the FHIR record provides "gliclazide 40 mg" — the correct name and dose reach the document generator regardless.

**Agent 3 — Contextual inference (MedGemma 27B).** The document generation model receives both the transcript and the structured EHR context. As a large language model, it can resolve ambiguous or corrupted tokens against the clinical context (e.g., inferring that "regar" in the context of renal monitoring refers to eGFR). The Jinja2 prompt template explicitly instructs the model to cross-reference transcript content against EHR data and flag discrepancies.

**Human-in-the-loop review.** All generated documents pass through a mandatory clinician review screen before finalisation. The clinician can edit any section, correct errors, and must explicitly sign off before the document is exported. This final checkpoint ensures that no transcription error reaches the patient record uncorrected.

### 1.7 Limitations

**Synthetic audio.** TTS speech is clean, consistently paced, and accent-uniform. Real clinical consultations involve background noise, speaker overlap, hesitations, self-corrections, and diverse accents. Production WER would likely be higher.

**Single speaker.** All clips use one synthetic voice. A deployed system must handle multiple speakers within a single consultation (doctor and patient), varied accents, and age-related speech differences.

**Limited corpus size.** Three clips totalling 644 words provide a directional estimate, not a statistically robust confidence interval. Clinical deployment would require evaluation on hundreds of clips.

**No baseline comparison.** We did not benchmark Whisper large-v3 on the same clips, which would contextualise MedASR's performance relative to a general-purpose ASR model on medical content.

### 1.8 Future Work

1. **Real clinical audio evaluation.** Partner with NHS trusts to obtain de-identified consultation recordings, enabling WER measurement under authentic acoustic conditions.
2. **Whisper baseline comparison.** Run Whisper large-v3 on the identical test clips to quantify MedASR's advantage on medical terminology — we hypothesise MedASR will show lower error rates on drug names, conditions, and clinical abbreviations.
3. **Accent diversity.** Evaluate on clips with British regional accents (Scottish, Welsh, South Asian British English) to characterise performance variation across the NHS workforce.
4. **Larger test corpus.** Expand to 50+ clips across 10+ clinical specialties (cardiology, respiratory, endocrine, mental health, paediatrics) to establish specialty-specific WER baselines.
5. **Domain-adaptive fine-tuning.** Fine-tune MedASR on NHS-specific vocabulary (BNF drug names, SNOMED-CT terms, NHS organisational language) using CTC loss to reduce errors on the long tail of medical terminology.
6. **End-to-end pipeline evaluation.** Measure how transcription errors propagate through the full pipeline by comparing final document accuracy (BLEU, ROUGE-L, clinical fact recall) with perfect vs. MedASR-generated transcripts.
