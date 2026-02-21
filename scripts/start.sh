#!/bin/bash
set -e

echo "Starting Clarke..."

# Run LoRA training ONLY if flag is set
# Wrapped so failure NEVER prevents app startup
if [ "${RUN_LORA_TRAINING}" = "true" ]; then
    echo "============================================"
    echo "LoRA training requested. Running..."
    echo "============================================"
    python scripts/train_lora.py || echo "WARNING: Training failed but app will start normally"
    echo "============================================"
    echo "Training phase complete. Starting app..."
    echo "============================================"
fi

echo "USE_MOCK_FHIR=${USE_MOCK_FHIR:-false}"
echo "MEDASR_MODEL_ID=${MEDASR_MODEL_ID:-not set}"

python -m backend.fhir.mock_api &
FHIR_PID=$!
echo "Mock FHIR server started (PID: ${FHIR_PID})"
sleep 2
python app.py
