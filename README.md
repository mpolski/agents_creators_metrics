# Agents Creator Metrics

## Overview
This project provides a robust, automated pipeline to export analytics metrics from **Google Gemini Enterprise (Discovery Engine) Analytics** to **BigQuery**, while overcoming a native limitations in Gemini Enterprise Analytics while it's still in preview.

### The Problem
Currently, the native Gemini Enterprise Analytics UI lack two critical dimensions:
1. **Human-Readable Agent Names:** Data is only tracked against an opaque `Agent ID`, not the actual display name of the agent (e.g. "Shipping Cost Analyzer").
2. **Creator Accountability:** It is natively impossible to see *who* created an agent and *when* it was created directly within the analytics suite.

### The Solution
We solve this by actively combining data from the **Discovery Engine API** and Google Cloud **Audit Logs** to construct a unified analytics hub in BigQuery. Once the data is enriched and centralized in BigQuery, we deploy an **ADK-based conversational agent** to unlock the true potential of the data—allowing non-technical users to interact with and query these complex metrics entirely using native natural language.

![Diagram](./images/diagram.png)

---

## Phase 1: Data Pipeline & BigQuery Infrastructure

### Data Architecture
The data pipeline exports, enriches, and merges disparate data streams into three distinct tables stored within a single BigQuery dataset (default: `gemini_analytics`):

1. **`monthly_leaderboard`**
   - **Source:** Discovery Engine API (`exportMetrics`)
   - **Purpose:** Stores raw session and usage metrics (e.g., `agent_session_count`, `search_click_count`) grouped by `date` for activity reporting.
2. **`agent_names`**
   - **Source:** Discovery Engine API (`Assistants/Agents enumeration`)
   - **Purpose:** Maps opaque backend node IDs to human-readable agent `display_name`s.
3. **`historical_creators`**
   - **Source:** Google Cloud Audit Logs
   - **Purpose:** Maps agent IDs to their explicit creator email (`creator_email`) and creation `timestamp`.

*Note: We seamlessly join these tables in BigQuery by extracting the `agent_id` substring from the end of the `agent_name` column in the `monthly_leaderboard` table.*

Required Roles:
- **Discovery Engine Viewer/Editor** (`roles/discoveryengine.viewer`) - To read agent metadata and trigger metrics export.
- **Logs Configuration Writer** (`roles/logging.configWriter`) - To create the log sink.
- **Service Usage Admin** (`roles/serviceusage.serviceUsageAdmin`) - To enable the BigQuery API if not already enabled.
- **BigQuery Data Owner** (`roles/bigquery.dataOwner`) - To create the dataset/tables and populate them.
- **BigQuery Job User** (`roles/bigquery.jobUser`) - To run load jobs to push data to BigQuery.
- **Project IAM Admin** (`roles/resourcemanager.projectIamAdmin`) - Needed specifically to grant the auto-generated service account access to the BigQuery dataset (required only for `infra_setup/setup_sink.sh`).

**2. The Log Sink Service Account**
Running `infra_setup/setup_sink.sh` provisions a unique Writer Identity for the sink. You must ensure it has **BigQuery Data Editor** access to the dataset in the Analytics project.
- The script attempts to grant this automatically if you have Project IAM Admin on the Analytics project.
- If it fails (e.g., due to lack of permissions), it will print the exact `gcloud` command for an administrator to run manually.

### Pipeline Setup & Installation (One-Time)

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd business_value_agent
   ```

2. **Navigate to the `analytics_pipeline` directory:**
   ```bash
   cd analytics_pipeline
   ```

3. **Configure the Environment:**
   ```bash
   cp .env_template .env
   ```
   Define your active `PROJECT_ID`, engine info, and dataset specifications inside `.env`.

   **Enable BigQuery API in Analytics Project:**
   ```bash
   gcloud services enable bigquery.googleapis.com --project=PROJECT_ID
   ```

4. **Install Python Dependencies (using `uv`):**
   ```bash
   uv venv
   uv pip install -r data_pipelines/requirements.txt
   ```

### Infrastructure Setup

Run these steps to provision the required cloud infrastructure:

1. **Provision BigQuery Dataset and Metrics Table:**
   Initializes the BigQuery dataset and creates the metrics table (`monthly_leaderboard`).
   ```bash
   chmod +x infra_setup/setup_bq.sh
   ./infra_setup/setup_bq.sh
   ```

2. **Provision Cloud Logging Sink:**
   Creates the Cloud Logging sink to capture agent creation events and grants necessary permissions. *Note: Cloud Logging uses an auto-generated Google-managed service account like `service-[PROJECT_NUMBER]@gcp-sa-logging.iam.gserviceaccount.com` (Writer Identity) to deliver logs.*
   ```bash
   chmod +x infra_setup/setup_sink.sh
   ./infra_setup/setup_sink.sh
   ```

### Initial Data Ingestion & View Creation

Once the infrastructure is ready, run these steps to populate the dataset and create the unified view:

1. **First-time Data Sync:**
   Queries the Discovery Engine API to fetch metadata for all agents and triggers the first metrics export.
   ```bash
   .venv/bin/python data_pipelines/fetch_agent_names.py
   .venv/bin/python data_pipelines/metrics_to_bq.py
   ```

2. **One-Time Backfill of Historical Creators:**
   Scans past 365 days of Audit Logs to backfill `historical_creators` table.
   ```bash
   chmod +x data_pipelines/export_historical_creators.sh
   ./data_pipelines/export_historical_creators.sh
   ```
   *Note: This task may take several minutes to complete.*

3. **Create Unified Metrics View:**
   Creates a BigQuery view that joins the leaderboard data from logs with the agent names for full visibility.
   ```bash
   chmod +x infra_setup/create_unified_view.sh
   ./infra_setup/create_unified_view.sh
   ```

### Future Data Synchronization

To keep your analytics fresh, you should schedule the unified sync script to run periodically (e.g., nightly).

The `data_pipelines/sync_data.sh` script runs both `fetch_agent_names.py` and `metrics_to_bq.py` (same as Step 1 under Initial Data Ingestion & View Creation above).

1. **Run the Unified Sync Script:**
   ```bash
   chmod +x data_pipelines/sync_data.sh
   ./data_pipelines/sync_data.sh
   ```

#### How to Schedule It:

Here are a few common mechanisms to set this up:

**Option 1: Linux Cron (Simple, for local or VM execution)**
Add a cron job to run the script every night at midnight:
```bash
0 0 * * * cd /path/to/business_value_agent/analytics_pipeline && ./data_pipelines/sync_data.sh >> sync.log 2>&1
```

**Option 2: Cloud Run Jobs + Cloud Scheduler (Serverless, Recommended for Production)**
1.  Containerize the script (create a Dockerfile that installs dependencies and runs `sync_data.sh`).
2.  Deploy it as a **Cloud Run Job**.
3.  Use **Cloud Scheduler** to trigger the job nightly via an HTTP or workflow trigger.

**Option 3: Cloud Composer (Apache Airflow)**
If you are already using Airflow, you can create a simple DAG with a `BashOperator` to run this script on a schedule.

---

## Phase 2: Local Analytics Agent (ADK)

Once the data is flowing into BigQuery, this repository provides a powerful, pre-configured **Vertex AI Agent** built with the Agent Development Kit (ADK) capable of chatting with this data natively using the BigQuery MCP.

### The Vision: Empowering Change Management
Imagine deploying this ADK agent to **Vertex AI Agent Engine** and sharing its natural-language conversational interface directly with your Change Management, Platform Adoption, or Executive teams. Instead of manually writing SQL queries or building complex dashboards, non-technical stakeholders can simply ask the agent about specific data insights.
![ADK Agent Demo](./images/adk_agent_demo.png)

### Running the Agent
For detailed instructions on configuring the local environment, provisioning the ADK service account, and testing this ADK agent locally, refer to the [ADK Agent documentation](./adk_agent/README.md).
