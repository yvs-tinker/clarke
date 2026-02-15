#!/bin/bash
set -e

echo "Starting Clarke..."
echo "USE_MOCK_FHIR=${USE_MOCK_FHIR:-false}"
echo "MEDASR_MODEL_ID=${MEDASR_MODEL_ID:-not set}"

python app.py
