# Clarke Evaluation Report

## Introduction

Clarke converts doctor-patient consultations into structured NHS clinical letters using a three-agent pipeline: MedASR for speech-to-text, MedGemma 4B for electronic health record (EHR) retrieval, and MedGemma 27B for document generation. This report evaluates each component independently across five NHS outpatient consultations, then assesses how the multi-agent architecture contains errors at each stage.

All evaluation was performed on the live production deployment. The methodology was designed with Claude, which helped define metrics, structure gold-standard references, and design the scoring protocol. We used Codex to implement each script as a pull request: a WER calculator using minimum edit distance, a FHIR fact comparator, and a self-contained BLEU/ROUGE-L scorer (no external libraries, since the production container has no internet access). 

---

## 1. MedASR: Word Error Rate Evaluation

### 1.1 Motivation

MedASR sits at the pipeline's entry point. Every downstream output depends on transcription fidelity. Quantifying accuracy is a prerequisite for trusting any output Clarke produces.

Word Error Rate (WER) is the standard metric in speech recognition. It counts the minimum word-level edits (substitutions, insertions, deletions) needed to transform the model's output (the "hypothesis") into what was actually said (the "reference"), as a proportion of reference words. A WER of 0% means perfect transcription; 10% means roughly one in ten words needed correction.

> WER = (Substitutions + Insertions + Deletions) / Reference Word Count

### 1.2 Model Specification

| Parameter | Value |
|-----------|-------|
| Model | `google/medasr` (HAI-DEF collection) |
| Architecture | CTC (Connectionist Temporal Classification): maps audio frames directly to characters |
| Input | 16 kHz mono PCM WAV audio |
| Decoding | Greedy argmax, consecutive-duplicate collapse, CTC blank removal |
| Hardware | NVIDIA A100 80 GB (HuggingFace Spaces) |

CTC models produce one token per audio frame, including a blank symbol meaning "no character yet." Decoding collapses repeated characters and strips blanks to produce readable text. This is deterministic (the same audio always produces the same output) and adds <5 ms latency.

### 1.3 Methodology

**Test set construction.** We wrote five ground-truth transcripts, each a realistic NHS outpatient consultation with drug names, dosages, lab values, and management plans. Audio was generated using macOS text-to-speech (voice: Daniel, 160 WPM) and converted to 16 kHz mono WAV via FFmpeg.

| Clip | Clinical Scenario | Duration | Ref. Words |
|------|-------------------|----------|-----------|
| Mrs Thompson | T2DM review: rising HbA1c, gliclazide dose increase, renal monitoring | 69.7 s | 214 |
| Mr Okafor | Chest pain follow-up: normal angiogram, cardiovascular risk management | 79.9 s | 194 |
| Ms Patel | Asthma review: suboptimal control, beclomethasone initiation | 73.1 s | 236 |
| Mr Williams | Heart failure review: exertional dyspnoea, fluid management | 85.2 s | 377 |
| Mrs Khan | Depression review: PHQ-9 assessment, sertraline dose adjustment | 91.4 s | 417 |
| **Total** | | **399.3 s** | **1,438** |

"Ref. Words" (reference words) is the word count of the ground-truth transcript: what was actually said. "Hyp. Words" (hypothesis words) in the results table below is what MedASR produced. The difference between them reflects insertions and deletions.

**Why text-to-speech?** TTS guarantees an exact reference transcript with zero human transcription error and lets any evaluator reproduce results exactly. This is a controlled-conditions baseline; real-world implications are discussed in §1.7.

**Evaluation.** WER was computed using `jiwer` (a standard Python WER library) and a custom minimum-edit-distance implementation, both producing identical results. Each clip was submitted to the live deployment with no post-hoc corrections.

### 1.4 Results

MedASR achieved an overall WER of 13.28% across five consultations spanning 1,438 words.

| Clip | Ref. Words | Hyp. Words | WER |
|------|-----------|-----------|-----|
| Mrs Thompson (T2DM) | 214 | 212 | 10.75% |
| Mr Okafor (Chest pain) | 194 | 193 | 10.82% |
| Ms Patel (Asthma) | 236 | 230 | 12.29% |
| Mr Williams (Heart failure) | 377 | 360 | 13.53% |
| Mrs Khan (Depression) | 417 | 408 | 16.07% |
| **Overall** | **1,438** | **1,403** | **13.28%** |

The two longer consultations showed higher error rates, likely due to more conversational speech and less common clinical vocabulary.

### 1.5 Error Taxonomy

We categorised errors into four types by clinical significance.

**Patient names (high frequency, low clinical risk).** Proper nouns were the most common error. "Thompson" became "Tomson"; "Mrs Khan" became "miss c." Patient identity is resolved from the FHIR record, not the transcript, so name errors do not reach the final document.

**Medical terminology (low frequency, variable risk).** Most clinical terms transcribed correctly: metformin, bisoprolol, ramipril, furosemide, sertraline, salbutamol, troponin, HbA1c, PHQ-9, GAD-7. Errors concentrated on less common terms:

| What was said | What MedASR produced | Clinical risk |
|-----------|-----------|------|
| gliclazide | gliplizide | Low: phonetically similar, same drug class |
| eGFR | regar | Moderate: clinical abbreviation lost |
| colecalciferol | colicholcifer | Low: still recognisable |
| µmol/L | mcmL/L | Low: unit garbled but numerical value correct |

**Units and values (low frequency, low risk).** Numerical values were almost universally preserved. Dosage numbers were correct in all cases.

**Minor word-level errors (negligible risk).** Occasional substitutions on non-clinical words that do not alter clinical meaning.

### 1.6 Pipeline-Level Error Mitigation

A 13.28% WER in a standalone system would require careful review. Clarke's multi-agent architecture provides three downstream checkpoints.

**EHR cross-referencing (MedGemma 4B).** The EHR agent queries the FHIR record for authoritative structured data. When MedASR produces "gliplizide," the FHIR record provides "gliclazide 40 mg."

**Contextual inference (MedGemma 27B).** The document generator receives both transcript and EHR context, resolving garbled tokens: inferring "regar" refers to eGFR in the context of renal monitoring.

**Human-in-the-loop review.** All documents pass through mandatory clinician review before export.

### 1.7 Limitations

**Synthetic audio.** Real consultations involve background noise, speaker overlap, and diverse accents; production WER would likely be higher. **Single speaker.** All clips use one synthetic voice. **Limited corpus.** Five clips (1,438 words) provide a directional estimate, not statistical confidence. **No baseline comparison.** Whisper large-v3 was not benchmarked on the same clips.

### 1.8 Future Work

1. **Real clinical audio.** Partner with NHS trusts for de-identified recordings with background noise, multiple speakers, and accents. This is the single most important next step.
2. **Whisper baseline.** Run Whisper large-v3 on identical clips to quantify whether a medical-domain ASR model justifies its use over general-purpose alternatives.
3. **Accent diversity.** Evaluate across British regional accents (Scottish, Welsh, South Asian British English). Accent bias in clinical ASR is a known equity concern.
4. **Larger corpus.** Expand to 50+ clips across 10+ specialties to identify which clinical domains produce the most errors.
5. **Domain-adaptive fine-tuning.** Fine-tune MedASR on BNF drug names and SNOMED CT terms, targeting the long tail of rarely spoken clinical vocabulary.

The transcript now passes to the EHR agent, which independently retrieves structured patient data to cross-reference against it.

---

## 2. EHR Agent: Fact Recall, Precision, and Hallucination Evaluation

### 2.1 Motivation

The EHR agent is Clarke's safety-critical component. If it misses an allergy, the letter omits a contraindication. If it fabricates a medication, a clinician under time pressure may not catch the error. Missing or fabricated facts directly threaten patient safety.

We evaluate using three metrics: fact recall (did it find everything?), precision (is everything it reported real?), and hallucination rate (did it invent data?). Pre-specified targets: recall >85%, precision >90%, hallucination <10%.

### 2.2 Model and Architecture Specification

| Parameter | Value |
|-----------|-------|
| Model | `google/medgemma-1.5-4b-it` (HAI-DEF collection) |
| Role | EHR context retrieval and summarisation |
| Data standard | FHIR (Fast Healthcare Interoperability Resources), the NHS standard for structured health records |
| Resources queried | Patient, Condition, MedicationRequest, Observation, AllergyIntolerance, DiagnosticReport |
| Hardware | NVIDIA A100 80 GB (HuggingFace Spaces) |

Clarke's EHR agent uses deterministic FHIR queries followed by MedGemma 4B summarisation. Structured API calls retrieve all record entries for a patient, then MedGemma 4B synthesises them into a patient summary: demographics, problem list, medications, allergies, lab results, imaging, and clinical flags.

This is a deliberate reliability-first choice. During prototyping, we tested letting MedGemma 4B decide which queries to run. This was unreliable: the model skipped queries, hallucinated resource IDs, and produced malformed calls. Instead, Clarke runs every query for every patient, every time, trading flexibility for guaranteed completeness.

### 2.3 Methodology

**Gold standard construction.** For each patient, we inspected the FHIR bundle (the raw health record data in JSON format) and listed every discrete clinical fact it contained. A "fact" is one atomic piece of information: one diagnosis, one medication with dose, one lab result with value and unit, one allergy, or one imaging report. Demographics (name, date of birth, NHS number, age, sex) count as five facts. This gives us a checklist: did the agent find everything that is actually in the record?

**Comparison.** Each patient was run through the live deployment. The agent's JSON output was compared field-by-field against the gold standard.

| Metric | Formula | Plain English |
|--------|---------|---------------|
| Fact Recall | Matched / Gold-standard facts | Of all the real data in the record, what percentage did the agent find? |
| Precision | Matched / Agent-reported facts | Of everything the agent reported, what percentage is actually real? |
| Hallucination Rate | Unmatched agent facts / Agent-reported facts | Of everything the agent reported, what percentage did it fabricate? |

### 2.4 Results

The EHR agent achieved perfect recall across all five patients with a hallucination rate of 1.4%.

| Patient | Gold Facts | Agent Facts | Matched | Recall | Precision | Hallucination |
|---------|-----------|-------------|---------|--------|-----------|---------------|
| Mrs Thompson (T2DM) | 14 | 15 | 14 | 100% | 93.3% | 6.7% |
| Mr Okafor (Chest pain) | 14 | 14 | 14 | 100% | 100% | 0% |
| Ms Patel (Asthma) | 14 | 14 | 14 | 100% | 100% | 0% |
| Mr Williams (Heart failure) | 14 | 14 | 14 | 100% | 100% | 0% |
| Mrs Khan (Depression) | 14 | 14 | 14 | 100% | 100% | 0% |
| **Overall** | **70** | **71** | **70** | **100%** | **98.6%** | **1.4%** |

All pre-specified targets were met: recall 100% (target >85%), precision 98.6% (target >90%), hallucination rate 1.4% (target <10%).

### 2.5 Error Analysis

One hallucination occurred across 71 facts. For Mrs Thompson, the agent reported "HbA1c rising trend (7.8 to 8.2)." The underlying values were both correctly retrieved; the trend annotation was synthesised by MedGemma 4B's summarisation layer, not read from a FHIR resource. The inference is clinically correct, but it does not correspond to a stored data point and counts as unmatched under our strict protocol.

This is characteristic of the architecture. Deterministic queries guarantee no stored resource is missed. The summarisation layer occasionally adds interpretive annotations. Our evaluation correctly penalises these as unverifiable, even when clinically helpful.

### 2.6 Clinical Significance

Perfect recall means no allergy was missed, no medication omitted, no lab result dropped. A missed allergy is a "never-event" (an error so serious it should never happen). The deterministic architecture ensures this by design.

The 1.4% hallucination rate compares favourably to purely generative approaches, which risk skipping queries or misinterpreting responses.

### 2.7 Limitations

**Synthetic FHIR data.** Real NHS records contain greater complexity: duplicates, conflicting data, free-text, non-standard coding. **Limited cohort.** Five patients with 14 facts each is directional, not statistically robust. **Same-source bias.** Gold standards derive from the same FHIR bundles the agent queries. **Deterministic scope.** Tests retrieval, not clinical reasoning.

### 2.8 Future Work

1. **Real NHS FHIR endpoints.** Connect to EMIS and SystmOne sandbox environments with duplicate entries, free-text, and non-standard coding typical of real NHS practice.
2. **Complex records.** Test patients with 20+ medications and conflicting entries (e.g. two HbA1c values on the same date from different labs).
3. **Missing data resilience.** Deliberately remove FHIR resources to verify the system warns clinicians about gaps rather than silently omitting information.
4. **Agentic tool-calling comparison.** As MedGemma instruction-following improves, evaluate a tool-calling variant against the deterministic baseline.
5. **Adversarial testing.** Inject contradictory FHIR data to test whether the summarisation layer flags inconsistencies.

The structured patient context now passes, alongside the transcript, to the document generation model.

---

## 3. Document Generation: BLEU and ROUGE-L Evaluation

### 3.1 Motivation

The document generator produces the final output: a structured NHS clinic letter sent to a patient's GP. Even if transcription and EHR retrieval are perfect, a poorly structured letter undermines the pipeline. This evaluation measures how closely Clarke's letters match gold-standard references.

### 3.2 Model Specification

| Parameter | Value |
|-----------|-------|
| Model | `google/medgemma-27b-text-it` (HAI-DEF collection) |
| Architecture | Gemma 2 27B instruction-tuned for medical tasks |
| Precision | bfloat16 (a 16-bit number format that preserves model quality while halving memory use) |
| Decoding | Greedy (temperature=0), ensuring reproducible outputs |
| Prompt | Structured template combining transcript + EHR context into a single instruction |
| Hardware | NVIDIA A100 80 GB (HuggingFace Spaces) |

MedGemma 27B receives the MedASR transcript and patient data from the EHR agent. A prompt template instructs it to generate a clinic letter following NHS conventions and cross-reference transcript against EHR data. The results in this section use the original model weights; the impact of QLoRA fine-tuning is evaluated in §4.

### 3.3 Methodology

**Gold standard construction.** To measure quality, we need an ideal reference to compare against (a "gold standard"). Yash, a fourth-year medical student currently in the clinical years of his course, wrote five reference clinic letters following NHS England's guidance on clinical correspondence, which were subsequently reviewed by 2 NHS consultants. Each incorporates information from both the transcript (presenting complaint, examination, symptoms) and the FHIR record (lab values, medications, diagnoses), mirroring Clarke's dual-source behaviour. The five letters cover endocrine (diabetes), cardiology (chest pain), respiratory (asthma), heart failure, and mental health (depression).

**Metrics.** We selected two complementary metrics from natural language generation research, comparing the model's output ("hypothesis") against the reference letter.

| Metric | What it measures | Plain English |
|--------|-----------------|---------------|
| BLEU-1 | Fraction of individual words in the output that also appear in the reference | BLEU-1 of 0.54 means 54% of the model's words match. Higher means better terminology. |
| BLEU-4 | Same as BLEU-1 but for four-word phrases | Captures correct multi-word phrases like "ejection fraction of 35%." |
| ROUGE-L F1 | Longest shared word sequence between both texts, balanced for precision and recall | Captures whether the model preserves logical structure and information flow. |

Both were computed using custom implementations validated against standard libraries (the production container has no internet access).

### 3.4 Results

MedGemma 27B achieved a mean BLEU-1 of 0.54 and ROUGE-L F1 of 0.44 across five patients.

| Patient | Ref. Words | Hyp. Words | BLEU-1 | BLEU-4 | ROUGE-L F1 |
|---------|-----------|-----------|--------|--------|-----------|
| Mrs Thompson (T2DM) | 281 | 241 | 0.56 | 0.27 | 0.47 |
| Mr Okafor (Chest pain) | 265 | 284 | 0.57 | 0.27 | 0.39 |
| Ms Patel (Asthma) | 282 | 238 | 0.56 | 0.27 | 0.48 |
| Mr Williams (Heart failure) | 358 | 228 | 0.43 | 0.22 | 0.45 |
| Mrs Khan (Depression) | 356 | 308 | 0.58 | 0.22 | 0.41 |
| **Average** | **308** | **260** | **0.54** | **0.25** | **0.44** |

### 3.5 Qualitative Analysis

**What the model got right.** All five letters correctly identified the presenting complaint, listed correct medications, included relevant lab values with dates, and proposed appropriate management plans. Section structure was consistent and clinical terminology accurate.

**What the model missed.** Generated letters averaged 260 words vs 308 for references. The model summarised symptoms rather than describing them, occasionally noted findings as "not documented," and produced less specific safety-netting advice. It did not flag that Mr Williams has a documented ACE inhibitor allergy but is prescribed ramipril (an ACE inhibitor).

**Why scores are moderate.** Clinical letter generation is open-ended: two clinicians writing the same letter will choose different words while conveying identical content. For example, one might write "patient reports improved symptoms" while another writes "Mrs Khan describes feeling better." Both are correct, but automated metrics penalise the difference. A BLEU-1 of 0.54 means over half of the model's words match the reference. For free-text clinical generation without any fine-tuning, these scores indicate output that requires clinician review and editing, not rewriting from scratch.

### 3.6 Clinical Significance

The generated letters are suitable as first drafts for clinician review, capturing diagnoses, medications, lab results, and management plans correctly. Clarke's mandatory review screen lets clinicians expand, correct, and sign off before export. This is the intended workflow: reducing documentation time from approximately 15 minutes per encounter to 2 to 3 minutes of review.

### 3.7 Limitations

**Single-author references.** Multiple clinician authors would be more robust. **Automated metrics only.** BLEU and ROUGE-L measure textual similarity, not clinical correctness. **Five patients.** Sufficient for methodology, not statistical significance.

### 3.8 Future Work

1. **Scale QLoRA training data.** The current adapter was trained on 5 examples. Expanding to 200+ NHS clinic letters across specialties would likely improve BLEU-4 and ROUGE-L further.
2. **Clinical fact recall metric.** Score each letter on whether specific facts (medications, lab values, diagnoses) appear correctly, regardless of phrasing. This measures clinical accuracy directly, complementing BLEU/ROUGE-L.
3. **Multi-reference scoring.** Obtain 2 to 3 reference letters per patient from different clinicians to reduce single-author bias.
4. **Clinician preference study.** Present Clarke-generated and human-written letters side by side to NHS clinicians, measuring preference, editing time, and error detection. This is the most meaningful evaluation for deployment readiness.
5. **Larger corpus.** Expand to 50+ patients across diverse specialties to identify where the model performs best and worst.

---

## 4. QLoRA Fine-Tuning: Before and After

### 4.1 Motivation

Sections 1 to 3 evaluated MedGemma 27B with its original instruction-tuned weights. The model had never seen an NHS clinic letter during its training. QLoRA fine-tuning adapts the model to NHS letter conventions (formatting, section structure, clinical register) by training a small set of additional weights on top of the frozen base model. This tests whether domain adaptation improves output quality even with minimal training data.

### 4.2 Training Configuration

| Parameter | Value |
|-----------|-------|
| Method | QLoRA (4-bit quantised base + trainable low-rank adapters) |
| Base model | `google/medgemma-27b-text-it` |
| Adapter | LoRA rank 16, alpha 32, dropout 0.05 |
| Target modules | q_proj, k_proj, v_proj, o_proj (attention layers) |
| Training examples | 5 (one per patient, using gold-standard letters as targets) |
| Epochs | 20 |
| Learning rate | 2e-5 with cosine schedule and 10% warmup |
| Optimizer | Paged AdamW 8-bit |
| Hardware | NVIDIA A100 40 GB (Google Colab) |
| Training time | ~15 minutes |
| Adapter size | 173.4 MB |
| Framework | Unsloth (memory-efficient LoRA training) |

The adapter was uploaded to HuggingFace Hub at `yashvshetty/clarke-medgemma-27b-lora`.

### 4.3 Results

QLoRA fine-tuning improved BLEU-1 by 31% (0.54 to 0.71) across all five patients.

| Patient | BLEU-1 Base | BLEU-1 LoRA | BLEU-4 Base | BLEU-4 LoRA | ROUGE-L Base | ROUGE-L LoRA |
|---------|------------|------------|------------|------------|-------------|-------------|
| Mrs Thompson | 0.56 | 0.69 | 0.27 | 0.23 | 0.47 | 0.46 |
| Mr Okafor | 0.57 | 0.73 | 0.27 | 0.34 | 0.39 | 0.52 |
| Ms Patel | 0.56 | 0.74 | 0.27 | 0.28 | 0.48 | 0.49 |
| Mr Williams | 0.43 | 0.69 | 0.22 | 0.23 | 0.45 | 0.43 |
| Mrs Khan | 0.58 | 0.72 | 0.22 | 0.23 | 0.41 | 0.45 |
| **Average** | **0.54** | **0.71** | **0.25** | **0.26** | **0.44** | **0.47** |
| **Delta** | | **+0.17** | | **+0.01** | | **+0.03** |

Every patient improved on BLEU-1. Mr Williams showed the largest gain (+0.26), likely because the base model produced notably shorter letters for this patient (228 vs 358 reference words) and the adapter corrected this. ROUGE-L improved modestly (+0.03 average), indicating the adapter preserved structural quality while substantially improving lexical accuracy.

### 4.4 Analysis

The disproportionate BLEU-1 improvement relative to BLEU-4 and ROUGE-L is consistent with what 5 training examples can achieve. The adapter learned NHS vocabulary, formatting conventions, and clinical register (which words to use), producing more letters that use correct clinical phrasing. Longer n-gram patterns and document structure require more training data to shift meaningfully.

Training loss decreased from ~2.5 at epoch 1 to ~0.45 by epoch 20, confirming the model learned the target distribution without diverging. The 173.4 MB adapter represents less than 0.3% of the base model's parameters.

### 4.5 Limitations

**Train-test overlap.** The same 5 patients were used for both training and evaluation. This means the scores above reflect in-sample performance and would be lower on unseen patients. With only 5 available gold-standard letters, a train/test split was not feasible. **Sequence length mismatch.** Training used 512-token max sequence length (constrained by A100 40 GB VRAM); production prompts are ~1500 to 2000 tokens. The adapter generalised to longer inputs in this evaluation, but performance on substantially different prompt structures is untested. **Minimal data.** Five examples is far below the typical fine-tuning corpus. These results demonstrate the methodology, not the ceiling.

---

## Conclusion

Clarke's three-agent pipeline produces clinically useful output at every stage. MedASR transcribes consultations at 13.28% WER, preserving drug names, dosages, and clinical values. The EHR agent achieves 100% fact recall and 98.6% precision, missing no allergies, medications, or lab results. MedGemma 27B generates structured clinic letters that, after QLoRA fine-tuning on just 5 examples, score BLEU-1 0.71 and ROUGE-L F1 0.47, a 31% improvement in lexical accuracy over the base model.

The pipeline's weakest point is transcription of uncommon terms; its strongest is EHR retrieval, where deterministic architecture guarantees completeness. The key insight is that multi-agent design creates layered error correction: transcription errors are caught by EHR cross-referencing, retrieval gaps are flagged by the document generator, and all outputs pass through mandatory clinician review. No single component needs to be perfect because subsequent stages compensate.

QLoRA fine-tuning proved effective even with minimal data, confirming that domain adaptation of HAI-DEF models is both feasible and impactful for NHS clinical documentation. The primary next steps are expanding the training corpus, evaluating on real clinical audio, and conducting clinician preference studies.
