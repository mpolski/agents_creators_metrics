#!/bin/bash
# deploy/create_unified_view.sh - Creates a unified view in BigQuery for aggregated metrics.

set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  echo "🔍 Loading environment variables from .env"
  set -a
  source .env
  set +a
else
  echo "⚠️ .env file not found."
fi

if [ -z "$BQ_DATASET_PROJECT_ID" ]; then
  BQ_DATASET_PROJECT_ID=$(gcloud config get-value project)
fi

PROJECT_ID=$BQ_DATASET_PROJECT_ID
DATASET_ID="gemini_analytics"
VIEW_ID="vw_unified_metrics"

echo "🚀 Creating BigQuery View: ${PROJECT_ID}.${DATASET_ID}.${VIEW_ID}"

bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET_ID}.${VIEW_ID}\` AS
SELECT 
  SPLIT(ml.agent_name, '/')[OFFSET(ARRAY_LENGTH(SPLIT(ml.agent_name, '/')) - 1)] as agent_id,
  an.display_name,
  SUM(ml.agent_session_count) as total_sessions,
  MAX(ml.monthly_agent_active_user_count) as monthly_users,
  MIN(ml.date) as first_active_date,
  MAX(ml.date) as last_active_date
FROM \`${PROJECT_ID}.${DATASET_ID}.monthly_leaderboard\` ml
JOIN \`${PROJECT_ID}.${DATASET_ID}.agent_names\` an 
  ON SPLIT(ml.agent_name, '/')[OFFSET(ARRAY_LENGTH(SPLIT(ml.agent_name, '/')) - 1)] = an.agent_id
GROUP BY agent_id, display_name
"

echo "✅ Success! Unified view created."
