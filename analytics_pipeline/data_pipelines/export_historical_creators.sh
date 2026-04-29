#!/bin/bash

# 1. Load variables from .env
set -a
source .env
set +a

RAW_FILE="raw_logs.json"
OUTPUT_FILE="historical_creators.jsonl"

echo "🔍 Scanning Cloud Audit Logs in project: ${PROJECT_ID} for historical agent creations (past 365 days)..."

# 2. Read the logs using the successful time-travel filter
gcloud logging read \
  'logName="projects/'"${PROJECT_ID}"'/logs/cloudaudit.googleapis.com%2Factivity" AND protoPayload.serviceName="discoveryengine.googleapis.com" AND protoPayload.methodName=~"CreateAgent"' \
  --project="${PROJECT_ID}" \
  --freshness=365d \
  --format="json" \
  --limit=10000 > "${RAW_FILE}"

# 3. Check if we actually got logs
if [ ! -s "${RAW_FILE}" ] || [ "$(cat ${RAW_FILE})" == "[]" ]; then
    echo "❌ No historical logs found or the file is empty."
    exit 1
fi

echo "✅ Raw logs downloaded! Now parsing with jq..."

# 4. Parse the raw file into JSON Lines, extracting exactly what we need
#    (Updated with safe fallbacks before splitting to prevent null string errors)
cat "${RAW_FILE}" | jq -c '.[]? | {
  timestamp: .timestamp,
  creator_email: (.protoPayload.authenticationInfo.principalEmail // (.protoPayload.authenticationInfo.principalSubject | sub("^user:"; "") | split("/") | last) // "unknown_email"),
  agent_id: ((.protoPayload.request.agent.name // .protoPayload.response.name // .protoPayload.resourceName // "unknown/unknown_id") | split("/") | last),
  display_name: (.protoPayload.request.agent.displayName // .protoPayload.response.displayName // "Unknown Name")
}' > "${OUTPUT_FILE}"

# 5. Verify the output and load to BigQuery
if [ -s "${OUTPUT_FILE}" ]; then
    echo "🎉 Success! Data parsed correctly. Here is a quick preview:"
    head -n 1 "${OUTPUT_FILE}" | jq .
    
    echo "🚀 Loading data into BigQuery table: ${PROJECT_ID}:${DATASET_ID}.historical_creators..."
    
    # 6. Load into BigQuery (using --replace so you can run this safely)
    bq load \
      --project_id="${PROJECT_ID}" \
      --source_format=NEWLINE_DELIMITED_JSON \
      --autodetect \
      --replace \
      "${PROJECT_ID}:${DATASET_ID}.historical_creators" \
      "${OUTPUT_FILE}"
      
    echo "✅ Historical backfill complete! Your data is now in BigQuery."
else
    echo "⚠️ jq couldn't map the fields correctly. The output file is empty."
fi