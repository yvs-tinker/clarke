# Clarke — Submission Checklist

## Ready Now (End of 24-Hour Build)
- [ ] Public HF Space: [URL pending] — accessible, runs 3 demo scenarios
- [ ] Public GitHub repo: [URL pending] — clean code, README, licence
- [ ] Public LoRA adapter: [Not published] (if trained) — traces to google/medgemma-27b-text-it
- [x] evaluation_report.md — metrics computed (if completed)

## Buffer Week (Mon 16 – Sun 22 Feb)
- [ ] 3-page writeup (Mon 16 Feb)
- [ ] 3-minute video (Tue 17 – Sat 21 Feb)
- [ ] Final Kaggle submission (Sun 22 Feb)
  - [ ] Writeup submitted via Kaggle Writeups tab
  - [ ] Agentic Workflow Prize selected
  - [ ] All links included: video, GitHub, HF Space, HF model

## Verification Notes (Task 37 run)
- HF Space and GitHub public URLs are not present in this repository snapshot; external incognito validation could not be completed in this environment.
- `evaluation_report.md` exists in repository root.

## Task 38 — Phase 5 Final Checkpoint (Current Repository Snapshot)

### Day 3 Criteria Verification
- [ ] Public HF Space is live and accessible from any browser. **Status: FAIL** (no public HF Space URL is present in `README.md` or this checklist).
- [ ] Public GitHub repo with clean code, README with architecture diagram, and docstrings. **Status: PARTIAL/FAIL** (README architecture diagram and licence are present, docstring scan passes, but no public GitHub URL is provided).
- [ ] At least 3 demo scenarios work flawlessly on the live HF Space. **Status: FAIL** (no live HF Space URL available for external verification).
- [ ] Submission checklist confirms all competition requirements are met (except video and writeup). **Status: FAIL** (`Ready Now` section still has unchecked public artefact items).

### Nice-to-Haves Inventory (for writeup/video planning)
- LoRA adapter trained and published? **N** (adapter publication skipped in current repo state).
- WER comparison table? **Y** (WER metrics recorded in `evaluation_report.md`).
- EHR Agent metrics? **Y** (fact recall/precision/hallucination metrics recorded).
- BLEU/ROUGE-L evaluation? **Y** (BLEU and ROUGE-L recorded).
- `evaluation_report.md` populated? **Y**.
- UI visually polished? **Y** (recorded as completed in Task 33 section of `evaluation_report.md`).

### Commands Used
```bash
rg -n "URL pending|add your public Space URL|<your-github-repo-url>" README.md submission_checklist.md
grep -rL '"""' backend/ frontend/ --include='*.py'
```
