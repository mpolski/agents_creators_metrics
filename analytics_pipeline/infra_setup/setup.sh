#!/bin/bash
# deploy/setup.sh - The single master script to provision everything in order.

set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  echo "🔍 Loading environment variables from .env"
  set -a
  source .env
  set +a
else
  echo "⚠️ .env file not found. Falling back to environment variables."
fi

# Fallback to gcloud if PROJECT_ID not set in .env
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project)
fi

# Fallback or default for DATASET_ID if not set
if [ -z "$DATASET_ID" ]; then
  DATASET_ID="gemini_analytics"
fi

echo "🚀 Step 1: Provisioning BigQuery Dataset and metrics table..."
chmod +x infra_setup/start.sh
./infra_setup/start.sh

echo "🚀 Step 2: Provisioning Cloud Logging Sink for live events..."
chmod +x infra_setup/setup_sink.sh
./infra_setup/setup_sink.sh

echo "🚀 Step 3: First-time Data Sync (creates agent_names table)..."
# Using absolute path to venv python for stability
.venv/bin/python data_pipelines/fetch_agent_names.py

echo "🚀 Step 4: Creating Unified Metrics View (now that tables exist!)..."
chmod +x infra_setup/create_unified_view.sh
./infra_setup/create_unified_view.sh

echo "✅ Success! Full environment and pipeline setup complete!"
