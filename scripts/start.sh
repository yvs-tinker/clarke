#!/bin/bash
set -e
export USER="${USER:-appuser}"
export TORCHINDUCTOR_CACHE_DIR="/tmp/torch_cache"

echo "Starting Clarke..."

if [ "${RUN_LORA_EVAL}" = "true" ]; then
    echo "============================================"
    echo "LoRA evaluation requested. Running..."
    echo "============================================"
    python scripts/eval_lora.py || echo "WARNING: Evaluation failed but app will start normally"
    echo "============================================"
    echo "Evaluation phase complete. Starting app..."
    echo "============================================"
fi

echo "USE_MOCK_FHIR=${USE_MOCK_FHIR:-false}"
echo "MEDASR_MODEL_ID=${MEDASR_MODEL_ID:-not set}"

python -m backend.fhir.mock_api &
FHIR_PID=$!
echo "Mock FHIR server started (PID: ${FHIR_PID})"
sleep 2
python app.py