#!/bin/bash
set -e
export USER="${USER:-appuser}"
export TORCHINDUCTOR_CACHE_DIR="/tmp/torch_cache"

echo "Starting Clarke..."
echo "USE_MOCK_FHIR=${USE_MOCK_FHIR:-false}"
echo "MEDASR_MODEL_ID=${MEDASR_MODEL_ID:-not set}"

python -m backend.fhir.mock_api &
FHIR_PID=$!
echo "Mock FHIR server started (PID: ${FHIR_PID})"
sleep 2
python app.py