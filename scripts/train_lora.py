"""One-shot LoRA training on HF Space A100, then push adapter to Hub."""
import os
os.environ["TORCHINDUCTOR_CACHE_DIR"] = "/tmp/torch_cache"
os.environ["USER"] = "appuser"
import gc
import json
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer
from datasets import Dataset
from jinja2 import Template

print("=" * 60)
print("CLARKE LoRA TRAINING - Starting")
print("=" * 60)

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

MODEL_ID = "google/medgemma-27b-text-it"
ADAPTER_REPO = "yashvshetty/clarke-medgemma-27b-lora"

template_text = Path("backend/prompts/document_generation.j2").read_text()
TEMPLATE = Template(template_text)

train_path = Path("data/training/train.jsonl")
records = [json.loads(line) for line in train_path.read_text().splitlines() if line.strip()]
print(f"Loaded {len(records)} training records")


def format_example(record):
    context_json = json.dumps(record["context"], ensure_ascii=False, indent=2)
    demo = record["context"]["demographics"]
    prompt = TEMPLATE.render(
        letter_date="18 Feb 2026",
        clinician_name="Dr Sarah Chen",
        clinician_title="Consultant, General Practice",
        gp_name="Dr Andrew Wilson",
        gp_address="Riverside Medical Practice",
        patient_name=demo["name"],
        patient_dob=demo.get("dob", ""),
        patient_nhs=demo.get("nhs_number", ""),
        transcript=record["transcript"],
        context_json=context_json,
    )
    return prompt + "\n" + record["reference_letter"].strip()


texts = [format_example(r) for r in records]
train_dataset = Dataset.from_dict({"text": texts})
print(f"Dataset: {len(train_dataset)} examples")

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading model in 4-bit...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
print(f"Model loaded. GPU memory: {torch.cuda.memory_allocated()/1e9:.1f} GB")

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)

training_args = TrainingArguments(
    output_dir="/tmp/clarke-lora-checkpoints",
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    logging_steps=1,
    save_strategy="no",
    report_to=[],
    bf16=True,
    optim="adamw_8bit",
    gradient_checkpointing=True,
)

trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset,
    processing_class=tokenizer,
    peft_config=peft_config,
    max_seq_length=2048,
    args=training_args,
)

print("Starting training...")
train_result = trainer.train()

loss_history = [entry["loss"] for entry in trainer.state.log_history if "loss" in entry]
print(f"Initial loss: {loss_history[0]:.4f}")
print(f"Final loss:   {loss_history[-1]:.4f}")

trainer.model.save_pretrained("/tmp/clarke-lora-adapter")
tokenizer.save_pretrained("/tmp/clarke-lora-adapter")
print("Adapter saved locally")

print(f"Pushing adapter to {ADAPTER_REPO}...")
trainer.model.push_to_hub(ADAPTER_REPO, commit_message="Updated LoRA: new section structure Feb 2026")
tokenizer.push_to_hub(ADAPTER_REPO, commit_message="Updated tokenizer Feb 2026")
print(f"Adapter pushed to {ADAPTER_REPO}")

metrics = {
    "initial_loss": float(loss_history[0]),
    "final_loss": float(loss_history[-1]),
    "epochs": 3,
    "lora_rank": 16,
    "samples": len(records),
}
print(f"TRAINING COMPLETE. Metrics: {json.dumps(metrics)}")

del model, trainer
gc.collect()
torch.cuda.empty_cache()
print("Memory freed.")
