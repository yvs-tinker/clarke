# Adapter output

No LoRA adapter weights are committed in-repo.

Task 28 training fallback was triggered in this environment because model downloads from Hugging Face were blocked (HTTP 403 via proxy). Per `clarke_PRD_tasks.md`, the workflow falls back to base `google/medgemma-27b-text-it` when LoRA training cannot complete after two attempts.

See `finetuning/adapter/task35_publication_status.md` for the Task 35 publication decision and verification evidence.
