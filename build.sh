#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e 

TOPIC=$1

if [ -z "$TOPIC" ]; then
  echo "[ERROR] Please provide a topic."
  echo "Usage: ./build.sh \"The Fermi Paradox\""
  exit 1
fi

echo "Starting Factory Pipeline for: $TOPIC"

# Activate virtual environment
source venv/bin/activate

# Run the modules sequentially
python3 02_draft.py "$TOPIC"
python3 03_generate_assets.py
python3 04_render.py

echo "Pipeline execution finished."