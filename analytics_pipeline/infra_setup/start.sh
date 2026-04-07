#!/bin/bash
# analytics_pipeline/infra_setup/start.sh - Initializes BigQuery dataset and table.

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

# Verify required variables
if [ -z "$PROJECT_ID" ] || [ -z "$DATASET_ID" ] || [ -z "$TABLE_ID" ]; then
  echo "❌ Error: Missing required variables (PROJECT_ID, DATASET_ID, TABLE_ID)."
  echo "Please check your .env file or environment variables."
  exit 1
fi

# Use BQ_LOCATION if set, fallback to US
LOCATION=${BQ_LOCATION:-US}

echo "🚀 Provisioning BigQuery Dataset and metrics table..."
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET_ID"
echo "Table: $TABLE_ID"
echo "Location: $LOCATION"

# Initialize the BigQuery Dataset
bq mk \
  --location=$LOCATION \
  --dataset \
  ${PROJECT_ID}:${DATASET_ID} || echo "⚠️ Dataset might already exist."

# Initialize the BigQuery Table
bq mk \
  --table \
  ${PROJECT_ID}:${DATASET_ID}.${TABLE_ID} || echo "⚠️ Table might already exist."

echo "✅ Success!"