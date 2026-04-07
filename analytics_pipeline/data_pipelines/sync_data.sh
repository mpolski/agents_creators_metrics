#!/bin/bash
# pipelines/sync_data.sh - Resumes periodic synchronization of display names and metrics.

set -e

echo "🔍 Syncing display names and metadata..."
.venv/bin/python analytics_pipeline/data_pipelines/fetch_agent_names.py

echo "📊 Syncing usage metrics..."
.venv/bin/python analytics_pipeline/data_pipelines/metrics_to_bq.py

echo "✅ Success! Periodic data synchronization complete."
