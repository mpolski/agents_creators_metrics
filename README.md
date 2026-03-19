# Agents Creator Metrics

## Overview
This project provides a robust, automated pipeline to export analytics metrics from **Google Gemini Enterprise (Discovery Engine) Analytics** to **BigQuery**, while overcoming a native limitations in Gemini Enterprise Analytics while it's still in preview.

### The Problem
Currently, the native Gemini Enterprise Analytics UI lack two critical dimensions:
1. **Human-Readable Agent Names:** Data is only tracked against an opaque `Engine ID`, not the actual display name of the agent (e.g. "Shipping Cost Analyzer").
2. **Creator Accountability:** It is natively impossible to see *who* created an agent and *when* it was created directly within the analytics suite.

### The Solution
We solve this by actively combining data from the **Discovery Engine API** and Google Cloud **Audit Logs** to construct a unified analytics hub in BigQuery. Once the data is enriched and centralized in BigQuery, we deploy an **ADK-based conversational agent** to unlock the true potential of the data—allowing non-technical users to interact with and query these complex metrics entirely using native natural language.

---

## Phase 1: Data Pipeline & BigQuery Infrastructure

### Data Architecture
The data pipeline exports, enriches, and merges disparate data streams into three distinct tables stored within a single BigQuery dataset (default: `gemini_analytics`):

1. **`monthly_leaderboard`** (Source: Discovery Engine API exportMetrics)
2. **`agent_names`** (Source: Discovery Engine API enumeration)
3. **`historical_creators`** (Source: Google Cloud Audit Logs)

*Note: We seamlessly join these tables in BigQuery by extracting the `agent_id` substring from the end of the `agent_name` column in the `monthly_leaderboard` table.*

### Infrastructure IAM & Security
When configuring the pipeline infrastructure, two core identities are used:

**1. The Operator (Your Local ADC)**
When executing setup scripts from your laptop via `gcloud auth application-default login`, you must have:
- **BigQuery Data Editor** (`roles/bigquery.dataEditor`)
- **Discovery Engine Viewer/Editor** (`roles/discoveryengine.viewer`)
- **Logs Configuration Writer / Viewer** (`roles/logging.configWriter`, `roles/logging.viewer`)
- **Project IAM Admin** (`roles/resourcemanager.projectIamAdmin`) required only for `setup_sink.sh`.

**2. The Log Sink Service Account**
Running `./setup_sink.sh` provisions a unique Writer Identity for the sink, automatically granting it **BigQuery Data Editor** to stream agent creations.

### Pipeline Setup & Installation

1. **Configure the Environment:**
   ```bash
   cp .env_template .env
   ```
   Define your active `PROJECT_ID`, engine info, and dataset specifications inside `.env`.

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **BigQuery Provisioning:**
   Execute the startup script to create the necessary dataset (`gemini_analytics`) and the base metrics table.
   ```bash
   ./start.sh
   ```

### Data Ingestion Steps
Run these targeted scripts to populate the tables:
1. **`python metrics_to_bq.py`**: Pushes raw Analytics metrics to `monthly_leaderboard`.
2. **`python fetch_agent_names.py`**: Extracts display names for `agent_names`.
3. **`./export_historical_creators.sh`**: Scans past 365 days of Audit Logs to backfill `historical_creators`.
4. **`./setup_sink.sh`**: Creates a live Logging Sink to stream *future* creations directly into BigQuery.

**Operational Cadence (Scheduling):**
Recommendation: Deploy `metrics_to_bq.py` and `fetch_agent_names.py` to **Google Cloud Run Jobs** and trigger them nightly via **Google Cloud Scheduler**.

---

## Phase 2: Local Analytics Agent (ADK)

Once the data is flowing into BigQuery, this repository provides a powerful, pre-configured **Vertex AI Agent** built with the Agent Development Kit (ADK) capable of chatting with this data natively using the BigQuery MCP.

### The Vision: Empowering Change Management
Imagine deploying this ADK agent to **Vertex AI Agent Engine** and sharing its natural-language conversational interface directly with your Change Management, Platform Adoption, or Executive teams. Instead of manually writing SQL queries or building complex dashboards, non-technical stakeholders can simply ask the agent about specific data insights.

![ADK Agent Demo](./images/adk_agent_demo.png)

### 1. Enable BigQuery MCP
You must explicitly enable the native BigQuery MCP service on your project infrastructure so the agent can discover BigQuery tools:
```bash
gcloud beta services mcp enable bigquery.googleapis.com --project="your-gcp-project-id"
```

### 2. ADK Agent Service Account & IAM
The `adk_agent` uses rigorous Service Account Impersonation to securely route to the managed BigQuery MCP and Vertex AI models. The Service Account defined in your `adk_agent/.env` as `TARGET_SA_EMAIL` must be explicitly granted the following roles.

**Quick SA Setup:**
Run these exact commands from your terminal to attach the required backend permissions to your Agent SA, as well as the explicit **Token Creator** permission for yourself to impersonate it:

```bash
export PROJECT_ID="your-gcp-project-id"
export ADK_SA="your-sa-name@$PROJECT_ID.iam.gserviceaccount.com"
export USER_EMAIL="your-google-email@domain.com"

# 1. Grant the agent access to Google Cloud
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ADK_SA" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ADK_SA" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ADK_SA" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ADK_SA" \
  --role="roles/bigquery.metadataViewer"
  
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ADK_SA" \
  --role="roles/mcp.toolUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ADK_SA" \
  --role="roles/serviceusage.serviceUsageConsumer"

# 2. Grant YOUR personal identity permission to impersonate the agent natively
gcloud iam service-accounts add-iam-policy-binding $ADK_SA \
  --member="user:$USER_EMAIL" \
  --role="roles/iam.serviceAccountTokenCreator"
```

### 3. Running the Agent
For detailed instructions on configuring the local environment, installing ADK dependencies, and testing this ADK agent locally, refer to the [ADK Agent documentation](./adk_agent/README.md).
