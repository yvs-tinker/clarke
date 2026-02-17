#!/bin/bash
set -e

echo "Starting Clarke..."
echo "USE_MOCK_FHIR=${USE_MOCK_FHIR:-false}"
echo "MEDASR_MODEL_ID=${MEDASR_MODEL_ID:-not set}"

# Start mock FHIR server in background so EHR agent has patient data to query.
# Runs on port 8080 (internal only); main app connects via localhost.
python -m backend.fhir.mock_api &
FHIR_PID=$!
echo "Mock FHIR server started (PID: ${FHIR_PID})"

# Brief pause to let FHIR server bind to port before main app starts querying it
sleep 2

python app.py
