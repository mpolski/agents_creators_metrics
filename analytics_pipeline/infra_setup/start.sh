# 1. List projects to find your target Project ID
gcloud projects list 

# 2. Set the active project (replace <YOUR_PROJECT_ID> with the actual ID)
gcloud config set project <YOUR_PROJECT_ID>

# 3. Export your environment variables
export PROJECT_ID=$(gcloud config get-value project)
export DATASET_ID=gemini_analytics
export TABLE_ID=monthly_leaderboard

# 4. Initialize the BigQuery Dataset
bq mk \
  --location=US \
  --dataset \
  ${PROJECT_ID}:${DATASET_ID}

# 5. Initialize the BigQuery Table
bq mk \
  --table \
  ${PROJECT_ID}:${DATASET_ID}.${TABLE_ID}