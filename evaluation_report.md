
## Task 29 — MedASR WER Evaluation
- Timestamp (UTC): 2026-02-14T16:41:08.050069+00:00
- Model: mock
- MedASR WER Average: 0.0000
- MedASR WER per clip:
  - mrs_thompson: WER=0.0000 (reference_words=214, hypothesis_words=214)
  - mr_okafor: WER=0.0000 (reference_words=194, hypothesis_words=194)
  - ms_patel: WER=0.0000 (reference_words=236, hypothesis_words=236)

## Task 30 — EHR Agent Fact Recall Evaluation
- Timestamp (UTC): 2026-02-14T17:01:27.245454+00:00
- Targets: recall > 85%, precision > 90%, hallucination < 10%
- Fact Recall Average: 1.0000
- Precision Average: 0.9867
- Hallucination Rate Average: 0.0133
- Target Status: recall=PASS, precision=PASS, hallucination=PASS
- Per-patient metrics:
  - pt-001: recall=1.0000, precision=0.9333, hallucination=0.0667 (matched=14, gold=14, output=15)
  - pt-002: recall=1.0000, precision=1.0000, hallucination=0.0000 (matched=14, gold=14, output=14)
  - pt-003: recall=1.0000, precision=1.0000, hallucination=0.0000 (matched=14, gold=14, output=14)
  - pt-004: recall=1.0000, precision=1.0000, hallucination=0.0000 (matched=15, gold=15, output=15)
  - pt-005: recall=1.0000, precision=1.0000, hallucination=0.0000 (matched=14, gold=14, output=14)

## Task 31 — Document Generation Evaluation
- Timestamp (UTC): 2026-02-14T17:16:52.406435+00:00
- Evaluated Samples: 50
- Model: mock
- BLEU: 0.5668
- ROUGE-L: 0.0977
- Manual Review (n=10): NHS format pass rate=100.00%, clinical accuracy pass rate=0.00%
- Fine-tuned comparison status: fine-tuned adapter not found (baseline-only evaluation)
