#!/bin/bash
# analytics_pipeline/infra_setup/setup_bq.sh - Initializes BigQuery dataset and table.

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
echo "🔍 Checking if dataset exists..."
if ! bq show ${PROJECT_ID}:${DATASET_ID} > /dev/null 2>&1; then
  echo "Creating dataset..."
  if ! bq mk --location=$LOCATION --dataset ${PROJECT_ID}:${DATASET_ID}; then
    echo "❌ Error: Failed to create dataset ${DATASET_ID}."
    exit 1
  fi
  echo "✅ Dataset created."
else
  echo "ℹ️ Dataset already exists."
fi

# Initialize the BigQuery Table
echo "🔍 Checking if table exists..."
if ! bq show ${PROJECT_ID}:${DATASET_ID}.${TABLE_ID} > /dev/null 2>&1; then
  echo "Creating table..."
  if ! bq mk --table ${PROJECT_ID}:${DATASET_ID}.${TABLE_ID}; then
    echo "❌ Error: Failed to create table ${TABLE_ID}."
    exit 1
  fi
  echo "✅ Table created."
else
  echo "ℹ️ Table already exists."
fi

echo "✅ Success!"