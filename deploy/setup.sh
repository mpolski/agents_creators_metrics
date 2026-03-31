#!/bin/bash
# deploy/setup.sh - The single master script to provision everything in order.

set -e

PROJECT_ID=$(gcloud config get-value project)
DATASET_ID="gemini_analytics"

echo "🚀 Step 1: Provisioning BigQuery Dataset and metrics table..."
chmod +x deploy/start.sh
./deploy/start.sh

echo "🚀 Step 2: Provisioning Cloud Logging Sink for live events..."
chmod +x deploy/setup_sink.sh
./deploy/setup_sink.sh

echo "🚀 Step 3: First-time Data Sync (creates agent_names table)..."
# Using absolute path to venv python for stability
.venv/bin/python pipelines/fetch_agent_names.py

echo "🚀 Step 4: Creating Unified Metrics View (now that tables exist!)..."
chmod +x deploy/create_unified_view.sh
./deploy/create_unified_view.sh

echo "✅ Success! Full environment and pipeline setup complete!"
