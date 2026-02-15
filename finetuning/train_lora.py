"""QLoRA fine-tuning entrypoint for MedGemma 27B clinical letter generation."""

from __future__ import annotations

import argparse
import gc
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.errors import ModelExecutionError, get_component_logger

logger = get_component_logger("train_lora")
PROMPT_TEMPLATE_PATH = Path("backend/prompts/document_generation.j2")
TRAINING_DATA_PATH = Path("data/training/train.jsonl")
ADAPTER_DIR = Path("finetuning/adapter")


@dataclass(frozen=True)
class FineTuneAttempt:
    """Container for a single LoRA training attempt hyper-parameter set.

    Args:
        lora_rank (int): Low-rank adaptation rank value.
        max_seq_length (int): Maximum sequence length for packing and truncation.
        sample_limit (int | None): Optional cap on loaded training records.

    Returns:
        FineTuneAttempt: Immutable attempt configuration object.
    """

    lora_rank: int
    max_seq_length: int
    sample_limit: int | None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for LoRA training orchestration.

    Args:
        None: Reads options from process command line.

    Returns:
        argparse.Namespace: Parsed arguments controlling runtime behaviour.
    """

    parser = argparse.ArgumentParser(description="Task 28: QLoRA fine-tuning for MedGemma 27B")
    parser.add_argument("--train-path", type=Path, default=TRAINING_DATA_PATH)
    parser.add_argument("--template-path", type=Path, default=PROMPT_TEMPLATE_PATH)
    parser.add_argument("--adapter-dir", type=Path, default=ADAPTER_DIR)
    parser.add_argument("--base-model", type=str, default=get_settings().MEDGEMMA_27B_MODEL_ID)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--use-tiny-model",
        action="store_true",
        help="Use a tiny public model for environment verification instead of MedGemma 27B.",
    )
    parser.add_argument("--use-wandb", action="store_true")
    return parser.parse_args()


def unload_other_models_for_training() -> None:
    """Release cached model state before loading MedGemma 27B for QLoRA training.

    Args:
        None: Performs global memory cleanup only.

    Returns:
        None: Frees Python and CUDA caches to minimise VRAM pressure.
    """

    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ModuleNotFoundError:
        logger.warning("torch is not installed; skipping CUDA cache clear")
    logger.info("Unloaded MedASR/MedGemma 4B placeholders and cleared caches before training")


def reload_runtime_models_after_training() -> None:
    """Log post-training model lifecycle step required by the PRD workflow.

    Args:
        None: No parameters.

    Returns:
        None: Emits instruction-level log for subsequent runtime reload.
    """

    logger.info("Post-training step complete; runtime should reload MedASR and MedGemma 4B on demand")


def load_training_records(train_path: Path, sample_limit: int | None = None) -> list[dict[str, Any]]:
    """Load JSONL triplets and optionally trim to a fixed sample count.

    Args:
        train_path (Path): Path to JSONL data with transcript/context/reference_letter keys.
        sample_limit (int | None): Optional maximum number of records to return.

    Returns:
        list[dict[str, Any]]: Parsed list of training samples.
    """

    if not train_path.exists():
        raise ModelExecutionError(f"Training dataset not found at {train_path}")

    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(train_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        item = json.loads(raw_line)
        missing_keys = {"transcript", "context", "reference_letter"} - set(item)
        if missing_keys:
            raise ModelExecutionError(
                f"Training sample at line {line_number} missing required keys: {sorted(missing_keys)}"
            )
        records.append(item)

    if sample_limit is not None:
        return records[:sample_limit]
    return records


def format_training_example(sample: dict[str, Any], prompt_template: str) -> str:
    """Convert one triplet into an instruction-tuning text sample.

    Args:
        sample (dict[str, Any]): Single JSON sample containing transcript/context/reference letter.
        prompt_template (str): Raw Jinja template text used as instruction scaffold.

    Returns:
        str: Prompt-completion text consumed by TRL SFT trainer.
    """

    context_json = json.dumps(sample["context"], ensure_ascii=False, indent=2)
    rendered_prompt = (
        prompt_template.replace("{{ transcript }}", sample["transcript"].strip())
        .replace("{{ context_json }}", context_json)
        .replace("{{ letter_date }}", "13 Feb 2026")
        .replace("{{ clinician_name }}", "Dr. Clarke")
        .replace("{{ clinician_title }}", "Consultant")
    )
    return f"{rendered_prompt}\n{sample['reference_letter'].strip()}"


def build_dataset(samples: list[dict[str, Any]], template_path: Path) -> Any:
    """Build a Hugging Face Dataset with formatted text examples for SFT.

    Args:
        samples (list[dict[str, Any]]): List of raw training triplets.
        template_path (Path): Path to document generation prompt template.

    Returns:
        Dataset: Dataset with single `text` column for SFTTrainer.
    """

    if not template_path.exists():
        raise ModelExecutionError(f"Prompt template not found at {template_path}")
    prompt_template = template_path.read_text(encoding="utf-8")
    from datasets import Dataset

    texts = [format_training_example(sample, prompt_template) for sample in samples]
    return Dataset.from_dict({"text": texts})


def build_attempt_sequence() -> list[FineTuneAttempt]:
    """Create primary and fallback attempt configurations as mandated in Task 28.

    Args:
        None: Uses static sequence from PRD fallback policy.

    Returns:
        list[FineTuneAttempt]: Ordered attempt list from default to reduced settings.
    """

    return [
        FineTuneAttempt(lora_rank=16, max_seq_length=4096, sample_limit=None),
        FineTuneAttempt(lora_rank=8, max_seq_length=2048, sample_limit=100),
    ]


def run_single_attempt(
    *,
    attempt: FineTuneAttempt,
    args: argparse.Namespace,
    settings: Any,
) -> dict[str, float]:
    """Execute one LoRA fine-tuning run and persist adapter artifacts.

    Args:
        attempt (FineTuneAttempt): Hyper-parameter profile for this run.
        args (argparse.Namespace): Parsed command-line runtime options.
        settings (Any): Application settings object with training defaults.

    Returns:
        dict[str, float]: Initial/final loss metrics for pass/fail checks.
    """

    model_id = "hf-internal-testing/tiny-random-gpt2" if args.use_tiny_model else args.base_model
    samples = load_training_records(args.train_path, sample_limit=attempt.sample_limit)
    if not samples:
        raise ModelExecutionError("Training dataset is empty")

    if args.dry_run:
        logger.info(
            "Dry run enabled; validated dataset/template only",
            sample_count=len(samples),
            lora_rank=attempt.lora_rank,
            max_seq_length=attempt.max_seq_length,
        )
        return {"initial_loss": 0.0, "final_loss": 0.0}

    import torch
    from peft import LoraConfig
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer

    dataset = build_dataset(samples, args.template_path)
    load_in_4bit = not args.use_tiny_model
    bnb_config = (
        BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        if load_in_4bit
        else None
    )

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict[str, Any] = {
        "device_map": "auto",
        "torch_dtype": torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    }
    if bnb_config is not None:
        model_kwargs["quantization_config"] = bnb_config

    model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)

    peft_config = LoraConfig(
        r=attempt.lora_rank,
        lora_alpha=settings.LORA_ALPHA,
        lora_dropout=settings.LORA_DROPOUT,
        bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )

    training_arguments = TrainingArguments(
        output_dir=str(args.adapter_dir / "checkpoints"),
        num_train_epochs=settings.TRAINING_EPOCHS,
        per_device_train_batch_size=settings.BATCH_SIZE,
        gradient_accumulation_steps=settings.GRAD_ACCUM_STEPS,
        learning_rate=settings.LEARNING_RATE,
        logging_steps=1,
        report_to=["wandb"] if args.use_wandb else [],
        max_steps=6 if args.use_tiny_model else -1,
        save_strategy="no",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        tokenizer=tokenizer,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=attempt.max_seq_length,
        args=training_arguments,
    )

    train_result = trainer.train()
    args.adapter_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(args.adapter_dir))
    tokenizer.save_pretrained(str(args.adapter_dir))

    loss_history = [entry["loss"] for entry in trainer.state.log_history if "loss" in entry]
    initial_loss = float(loss_history[0] if loss_history else train_result.training_loss)
    final_loss = float(loss_history[-1] if loss_history else train_result.training_loss)

    metrics = {"initial_loss": initial_loss, "final_loss": final_loss}
    (args.adapter_dir / "training_metrics.json").write_text(
        json.dumps(
            {
                **metrics,
                "sample_count": len(samples),
                "lora_rank": attempt.lora_rank,
                "max_seq_length": attempt.max_seq_length,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return metrics


def run_training(args: argparse.Namespace) -> int:
    """Run LoRA training with fallback attempts and PRD-compliant stop behaviour.

    Args:
        args (argparse.Namespace): Parsed CLI runtime options.

    Returns:
        int: Process exit code (0 success, 1 failure requiring fallback to base model).
    """

    settings = get_settings()
    unload_other_models_for_training()

    for attempt_index, attempt in enumerate(build_attempt_sequence(), start=1):
        try:
            logger.info(
                "Starting fine-tuning attempt",
                attempt=attempt_index,
                lora_rank=attempt.lora_rank,
                max_seq_length=attempt.max_seq_length,
                sample_limit=attempt.sample_limit,
            )
            metrics = run_single_attempt(attempt=attempt, args=args, settings=settings)
            logger.info(
                "Fine-tuning attempt complete",
                attempt=attempt_index,
                initial_loss=metrics["initial_loss"],
                final_loss=metrics["final_loss"],
            )
            reload_runtime_models_after_training()
            return 0
        except Exception as exc:  # noqa: BLE001
            logger.error("Fine-tuning attempt failed", attempt=attempt_index, error=str(exc))

    logger.error(
        "Known risk triggered. Switching to Fallback Path 3: use base MedGemma 27B without LoRA adapter."
    )
    reload_runtime_models_after_training()
    return 1


def main() -> int:
    """CLI entrypoint for Task 28 LoRA training workflow.

    Args:
        None: Reads command-line flags and runs training.

    Returns:
        int: Unix-style process status code.
    """

    args = parse_args()
    return run_training(args)


if __name__ == "__main__":
    raise SystemExit(main())
