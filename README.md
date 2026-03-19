# Discovery Engine Metrics to BigQuery Exporter

This project provides a script to export analytics metrics from a Google Cloud Discovery Engine to a BigQuery table.

## Prerequisites

- Python 3
- Google Cloud SDK (`gcloud`) installed and authenticated.
- You have run `gcloud auth application-default login`.

## Setup & Installation

1.  **Clone the repository (or download the files).**

2.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up BigQuery:**

    The `start.sh` script can be used to create the necessary BigQuery dataset and table.

    ```bash
    ./start.sh
    ```

4.  **Configure the environment:**

    Create a `.env` file by copying the template:

    ```bash
    cp .env_template .env
    ```

    Then, open the `.env` file and fill in your project details.

    ```
    # Google Cloud Project & App Config
    PROJECT_ID="your-gcp-project-id"
    GE_LOCATION="global"
    BQ_LOATOIN="us"
    ENGINE_ID="your-discovery-engine-id"

    # BigQuery Destination Config
    DATASET_ID="gemini_analytics"
    TABLE_ID="monthly_leaderboard"
    ```

## Usage

To export the metrics, run the `metrics_to_bq.py` script:

```bash
python metrics_to_bq.py
```

## File Descriptions

- `metrics_to_bq.py`: The main script to export metrics.
- `start.sh`: Setup script for BigQuery.
- `.env`: Configuration file.
- `requirements.txt`: Python dependencies.
- `README.md`: This file.

## Checking Operation Status

The export process is a long-running operation. The script will return an operation ID, which you can use to check the status of the export.

1.  **Paste the full operation ID you got from the script:**

    ```bash
    export OPERATION_NAME="projects/your-project-id/locations/global/collections/default_collection/engines/your-engine-id/operations/your-operation-id"
    ```

2.  **Grab your active project for the quota header:**

    ```bash
    export PROJECT_ID=$(gcloud config get-value project)
    ```

3.  **Fire the GET request to check the status:**

    ```bash
    curl -s -X GET \
      -H "Authorization: Bearer $(gcloud auth print-access-token)" \
      -H "x-goog-user-project: ${PROJECT_ID}" \
      "https://discoveryengine.googleapis.com/v1alpha/${OPERATION_NAME}"
    ```

    Look for the `"done": true` field in the response to confirm that the operation is complete.


# Part 2: Enriching Analytics with Agent Names and Creators

While the monthly leaderboard export gives us fantastic usage metrics, the data only contains raw `Engine IDs`. To make this actionable for business users, we need to map those IDs to human-readable **Agent Names** and track **Who Created Them**.

Because Google Cloud does not store a "Created By" field directly on the agent resource, we extract this information from **Cloud Audit Logs**. 

This guide sets up a two-part solution:
1.  **A Live Log Sink**: Automatically streams *future* agent creations directly into BigQuery.
2.  **A Historical Backfill**: Scans the past 365 days of logs to capture agents that *already* exist.

---

## Step 1: Update Your `.env` File

Add the `SINK_NAME` variable to the `.env` file you created in Part 1. It should look like this:

```env
# Google Cloud Project & App Config
PROJECT_ID="your-gcp-project-id"
GE_LOCATION="global"
BQ_LOCATION="us"
ENGINE_ID="your-discovery-engine-id"

# BigQuery Destination Config
DATASET_ID="gemini_analytics"
TABLE_ID="monthly_leaderboard"

# Log Sink Config
SINK_NAME="gemini_agent_creators"
