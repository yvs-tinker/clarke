"""Evaluate LoRA adapter by generating letters for all 5 patients and computing BLEU/ROUGE."""
import os
os.environ["TORCHINDUCTOR_CACHE_DIR"] = "/tmp/torch_cache"
os.environ["USER"] = os.environ.get("USER", "appuser")

import gc
import json
import re
import math
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
from jinja2 import Template

print("=" * 60)
print("CLARKE LoRA EVALUATION")
print("=" * 60)

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

MODEL_ID = "google/medgemma-27b-text-it"
ADAPTER_ID = "yashvshetty/clarke-medgemma-27b-lora"

# Load prompt template
template_text = Path("backend/prompts/document_generation.j2").read_text()
TEMPLATE = Template(template_text)

# Load gold standard references
GOLD_DIR = Path("evaluation/gold_standards")
REFERENCES = {}
for ref_file in sorted(GOLD_DIR.glob("ref_*.txt")):
    key = ref_file.stem.replace("ref_", "")
    REFERENCES[key] = ref_file.read_text(encoding="utf-8").strip()
print(f"Loaded {len(REFERENCES)} gold standard references: {list(REFERENCES.keys())}")

# Load FHIR bundles for patient context
FHIR_DIR = Path("data/fhir_bundles")
PATIENTS = {
    "mrs_thompson": "pt-001",
    "mr_okafor": "pt-002",
    "ms_patel": "pt-003",
    "mr_williams": "pt-004",
    "mrs_khan": "pt-005",
}

# Load transcripts
TRANSCRIPT_DIR = Path("data/demo")
TRANSCRIPTS = {}
for name, pt_id in PATIENTS.items():
    # Try different naming patterns
    for pattern in [f"{pt_id}_transcript.txt", f"{name}_transcript.txt"]:
        t_path = TRANSCRIPT_DIR / pattern
        if t_path.exists():
            TRANSCRIPTS[name] = t_path.read_text(encoding="utf-8").strip()
            break
print(f"Loaded {len(TRANSCRIPTS)} transcripts")

# Load FHIR contexts
def load_fhir_context(pt_id):
    bundle_path = FHIR_DIR / f"{pt_id}.json"
    if not bundle_path.exists():
        print(f"WARNING: No FHIR bundle for {pt_id}")
        return {}
    bundle = json.loads(bundle_path.read_text())
    # Extract key info from FHIR bundle
    context = {
        "patient_id": pt_id,
        "demographics": {},
        "problem_list": [],
        "medications": [],
        "allergies": [],
        "recent_labs": [],
        "recent_imaging": [],
    }
    if "entry" in bundle:
        for entry in bundle["entry"]:
            resource = entry.get("resource", {})
            rtype = resource.get("resourceType", "")
            if rtype == "Patient":
                name_parts = resource.get("name", [{}])[0]
                given = " ".join(name_parts.get("given", []))
                family = name_parts.get("family", "")
                prefix = name_parts.get("prefix", [""])[0] if name_parts.get("prefix") else ""
                context["demographics"]["name"] = f"{prefix} {given} {family}".strip()
                context["demographics"]["dob"] = resource.get("birthDate", "")
                nhs = ""
                for ident in resource.get("identifier", []):
                    if "nhs" in ident.get("system", "").lower():
                        nhs = ident.get("value", "")
                context["demographics"]["nhs_number"] = nhs
                context["demographics"]["sex"] = resource.get("gender", "").capitalize()
            elif rtype == "Condition":
                code = resource.get("code", {}).get("text", "")
                if not code:
                    codings = resource.get("code", {}).get("coding", [])
                    code = codings[0].get("display", "") if codings else ""
                if code:
                    context["problem_list"].append(code)
            elif rtype == "MedicationStatement" or rtype == "MedicationRequest":
                med_code = resource.get("medicationCodeableConcept", {})
                med_name = med_code.get("text", "")
                if not med_name:
                    codings = med_code.get("coding", [])
                    med_name = codings[0].get("display", "") if codings else ""
                dosage = resource.get("dosage", [{}])[0] if resource.get("dosage") else {}
                dose_text = dosage.get("text", "")
                context["medications"].append({"name": med_name, "dose": dose_text})
            elif rtype == "AllergyIntolerance":
                substance = resource.get("code", {}).get("text", "")
                if not substance:
                    codings = resource.get("code", {}).get("coding", [])
                    substance = codings[0].get("display", "") if codings else ""
                reaction_list = resource.get("reaction", [])
                reaction = ""
                if reaction_list:
                    manifestations = reaction_list[0].get("manifestation", [])
                    if manifestations:
                        reaction = manifestations[0].get("coding", [{}])[0].get("display", "")
                context["allergies"].append({"substance": substance, "reaction": reaction})
            elif rtype == "Observation":
                code = resource.get("code", {})
                obs_name = code.get("text", "")
                if not obs_name:
                    codings = code.get("coding", [])
                    obs_name = codings[0].get("display", "") if codings else ""
                value = ""
                unit = ""
                if "valueQuantity" in resource:
                    value = str(resource["valueQuantity"].get("value", ""))
                    unit = resource["valueQuantity"].get("unit", "")
                elif "valueString" in resource:
                    value = resource["valueString"]
                date = resource.get("effectiveDateTime", "")
                context["recent_labs"].append({"name": obs_name, "value": value, "unit": unit, "date": date})
            elif rtype == "DiagnosticReport":
                code = resource.get("code", {})
                report_name = code.get("text", "")
                if not report_name:
                    codings = code.get("coding", [])
                    report_name = codings[0].get("display", "") if codings else ""
                conclusion = resource.get("conclusion", "")
                date = resource.get("effectiveDateTime", resource.get("issued", ""))
                context["recent_imaging"].append({"type": report_name, "date": date, "summary": conclusion})
    return context

CONTEXTS = {}
for name, pt_id in PATIENTS.items():
    CONTEXTS[name] = load_fhir_context(pt_id)
print(f"Loaded {len(CONTEXTS)} FHIR contexts")

# Evaluation functions
def tokenize_text(text):
    return re.findall(r'\b\w+\b', text.lower())

def ngrams(tokens, n):
    return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def bleu_score(reference, hypothesis, max_n=4):
    ref_tokens = tokenize_text(reference)
    hyp_tokens = tokenize_text(hypothesis)
    if not hyp_tokens:
        return {"bleu1": 0.0, "bleu4": 0.0}
    log_avg = 0.0
    bleu1_val = 0.0
    for n in range(1, max_n+1):
        ref_ng = Counter(ngrams(ref_tokens, n))
        hyp_ng = Counter(ngrams(hyp_tokens, n))
        clipped = sum(min(hyp_ng[ng], ref_ng[ng]) for ng in hyp_ng)
        total = sum(hyp_ng.values())
        precision = clipped / total if total > 0 else 0.0
        if n == 1:
            bleu1_val = round(precision, 4)
        log_avg += math.log(precision) if precision > 0 else float('-inf')
    bp = min(1.0, math.exp(1 - len(ref_tokens)/len(hyp_tokens))) if len(hyp_tokens) > 0 else 0.0
    cumulative = bp * math.exp(log_avg / max_n) if log_avg > float('-inf') else 0.0
    return {"bleu1": bleu1_val, "bleu4": round(cumulative, 4)}

def rouge_l_f1(reference, hypothesis):
    ref_tokens = tokenize_text(reference)
    hyp_tokens = tokenize_text(hypothesis)
    if not ref_tokens or not hyp_tokens:
        return 0.0
    m, n = len(ref_tokens), len(hyp_tokens)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if ref_tokens[i-1] == hyp_tokens[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    lcs = dp[m][n]
    precision = lcs / n
    recall = lcs / m
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)

# Load model
print("\nLoading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

print("Loading base model in 4-bit...")
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

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(model, ADAPTER_ID)
model.eval()
print(f"Model + adapter loaded. GPU memory: {torch.cuda.memory_allocated()/1e9:.1f} GB")

# Generate letters
generated_letters = {}
for name in PATIENTS:
    if name not in TRANSCRIPTS:
        print(f"SKIP {name}: no transcript")
        continue
    if name not in CONTEXTS:
        print(f"SKIP {name}: no context")
        continue

    print(f"\nGenerating letter for: {name}")
    context = CONTEXTS[name]
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    demo = context.get("demographics", {})

    prompt = TEMPLATE.render(
        letter_date=datetime.now(tz=timezone.utc).strftime("%d %b %Y"),
        clinician_name="Dr Sarah Chen",
        clinician_title="Consultant, General Practice",
        gp_name="Dr Andrew Wilson",
        gp_address="Riverside Medical Practice",
        patient_name=demo.get("name", ""),
        patient_dob=demo.get("dob", ""),
        patient_nhs=demo.get("nhs_number", ""),
        transcript=TRANSCRIPTS[name],
        context_json=context_json,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False,
            repetition_penalty=1.1,
        )

    full_output = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    if full_output.startswith(prompt):
        letter = full_output[len(prompt):].strip()
    else:
        letter = full_output.strip()

    generated_letters[name] = letter
    word_count = len(tokenize_text(letter))
    print(f"  Generated {word_count} words")

# Evaluate
BASELINE = {
    "mrs_thompson": {"bleu1": 0.7970, "bleu4": 0.4882, "rouge_l": 0.6958},
    "mr_okafor":    {"bleu1": 0.7971, "bleu4": 0.6220, "rouge_l": 0.7247},
    "ms_patel":     {"bleu1": 0.8117, "bleu4": 0.5608, "rouge_l": 0.7119},
    "mr_williams":  {"bleu1": 0.8754, "bleu4": 0.7386, "rouge_l": 0.8139},
    "mrs_khan":     {"bleu1": 0.8244, "bleu4": 0.6425, "rouge_l": 0.7513},
}

print("\n" + "="*80)
print("EVALUATION RESULTS: LoRA Adapter vs Base Model (no adapter)")
print("="*80)
print(f"\n{'Patient':<20} {'Metric':<10} {'Base':<10} {'LoRA':<10} {'Delta':<10}")
print("-"*60)

lora_totals = {"bleu1": 0, "bleu4": 0, "rouge_l": 0}
base_totals = {"bleu1": 0, "bleu4": 0, "rouge_l": 0}
count = 0

for name in PATIENTS:
    if name not in generated_letters or name not in REFERENCES:
        continue
    ref = REFERENCES[name]
    hyp = generated_letters[name]
    bl = bleu_score(ref, hyp)
    rl = rouge_l_f1(ref, hyp)
    scores = {"bleu1": bl["bleu1"], "bleu4": bl["bleu4"], "rouge_l": rl}
    base = BASELINE.get(name, {"bleu1": 0, "bleu4": 0, "rouge_l": 0})

    for metric in ["bleu1", "bleu4", "rouge_l"]:
        delta = scores[metric] - base[metric]
        sign = "+" if delta >= 0 else ""
        label = {"bleu1": "BLEU-1", "bleu4": "BLEU-4", "rouge_l": "ROUGE-L"}[metric]
        print(f"{name:<20} {label:<10} {base[metric]:<10.4f} {scores[metric]:<10.4f} {sign}{delta:.4f}")
        lora_totals[metric] += scores[metric]
        base_totals[metric] += base[metric]
    count += 1
    print()

if count > 0:
    print("-"*60)
    print(f"{'AVERAGE':<20} {'Metric':<10} {'Base':<10} {'LoRA':<10} {'Delta':<10}")
    print("-"*60)
    for metric in ["bleu1", "bleu4", "rouge_l"]:
        avg_base = base_totals[metric] / count
        avg_lora = lora_totals[metric] / count
        delta = avg_lora - avg_base
        sign = "+" if delta >= 0 else ""
        label = {"bleu1": "BLEU-1", "bleu4": "BLEU-4", "rouge_l": "ROUGE-L"}[metric]
        print(f"{'AVERAGE':<20} {label:<10} {avg_base:<10.4f} {avg_lora:<10.4f} {sign}{delta:.4f}")

# Save generated letters
for name, letter in generated_letters.items():
    Path(f"/tmp/lora_{name}.txt").write_text(letter)
    print(f"Saved: /tmp/lora_{name}.txt")

print("\nEVALUATION COMPLETE.")

# Cleanup
del model
gc.collect()
torch.cuda.empty_cache()
print("Memory freed.")
