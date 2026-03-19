# Agents Creator Metrics

## Overview
This project provides a robust, automated pipeline to export analytics metrics from **Google Gemini Enterprise (Discovery Engine) Analytics** to **BigQuery**, while overcoming a native limitations in Gemini Enterprise Analytics while it's still in preview.

### The Problem
Currently, the native Gemini Enterprise Analytics exports lack two critical dimensions:
1. **Human-Readable Agent Names:** Data is only tracked against an opaque `Engine ID`, not the actual display name of the agent (e.g. "Cat Joke Teller").
2. **Creator Accountability:** It is natively impossible to see *who* created an agent and *when* it was created directly within the analytics suite.

### The Solution
We solve this by actively combining data from the **Discovery Engine API** and Google Cloud **Audit Logs** to construct a unified, actionable analytics hub in BigQuery. With this tool, your enterprise can monitor metrics across specific agents, track their specific creators, and evaluate agent lifecycles end-to-end.

---

## Data Architecture
The data pipeline exports, enriches, and merges disparate data streams into three distinct tables stored within a single BigQuery dataset (default: `gemini_analytics`):

1. **`monthly_leaderboard`**
   - **Source:** Discovery Engine API (exportMetrics).
   - **Purpose:** Contains all raw session and usage metrics (e.g. `agent_session_count`, `monthly_agent_active_user_count`, `search_click_count`) grouped by `date`. Includes the `agent_name` path string.
2. **`agent_names`**
   - **Source:** Discovery Engine API (Assistants & Agents enumeration).
   - **Purpose:** Maps specific unstructured agent IDs to human-readable `display_name`s.
3. **`historical_creators`**
   - **Source:** Google Cloud Audit Logs.
   - **Purpose:** Maps specific agent IDs to their creation `timestamp` and the specific `creator_email`.

*Note: You seamlessly join these tables in BigQuery by extracting the `agent_id` substring from the end of the `agent_name` column in the `monthly_leaderboard` table.*

---

## Google Cloud Services Used
This pipeline integrates several native Google Cloud products to build the analytics hub:
- **Discovery Engine API (Gemini Enterprise):** The source of the raw analytics metrics and the agent/assistant enumerations.
- **BigQuery:** The central data warehouse storing the three unified tables, and the provider of the native managed **BigQuery MCP** server.
- **Cloud Audit Logs:** Used to retrospectively and actively capture `CreateAgent` events.
- **Cloud Logging:** Leveraged to create a log sink that streams real-time agent creation logs directly to BigQuery.
- **Vertex AI (Agent Engine):** Used by the ADK local agent to converse naturally with the BigQuery MCP data.
- **Cloud Run & Cloud Scheduler:** (Recommended) Used to package and automate the extraction scripts on a regular cadence.

---

## Security & IAM Permissions

Because this pipeline connects several robust Google Cloud services natively, governing your Identity and Access Management (IAM) permissions correctly is essential—especially when running this from your laptop using Application Default Credentials (ADC) against Vertex AI.

### 1. The Operator (Your Local ADC)
When executing the setup scripts and manual backfills from your laptop, you run as yourself via `gcloud auth application-default login`. Your user account must have the following roles (or equivalent custom permissions) on your `PROJECT_ID`:
- **BigQuery Data Editor** (`roles/bigquery.dataEditor`): To construct the `gemini_analytics` dataset, create the leaderboard tables, and run the `bq load` / `gcloud` data commands.
- **Discovery Engine Viewer/Editor** (`roles/discoveryengine.viewer`): To invoke the `exportMetrics` API and list the Assistant/Agent hierarchy metadata.
- **Logs Configuration Writer** (`roles/logging.configWriter`): To formally create the cloud log routing sink (`setup_sink.sh`).
- **Logs Viewer** (`roles/logging.viewer`): To independently read the historical `CreateAgent` log streams in `export_historical_creators.sh`.
- **Project IAM Admin** (`roles/resourcemanager.projectIamAdmin`): Required **only** for `setup_sink.sh` to automatically attach BigQuery roles to the newly generated Google Sink Service Account.
- **Service Account Token Creator** (`roles/iam.serviceAccountTokenCreator`): Needed to successfully impersonate the ADK Agent Service Account (see below) from your local machine.

### 2. The Log Sink Service Account
When you run `./setup_sink.sh`, Google Cloud automatically provisions a unique Writer Identity (Service Account) dedicated to your new log sink. 
- The script automatically grants this robust SA **BigQuery Data Editor** on your project infrastructure so backend Google services can continuously stream new agent creations to your routing table without manual credentials.

### 3. The Local ADK Agent Service Account
The `adk_agent` uses rigorous Service Account Impersonation to securely route to the managed BigQuery MCP and Vertex AI LLMs. The Service Account defined in your `.env`'s `TARGET_SA_EMAIL` variable must be explicitly granted:
- **Vertex AI User** (`roles/aiplatform.user`): To natively query the Gemini models formatting your chat.
- **BigQuery Data Viewer** (`roles/bigquery.dataViewer`): Permits reading dataset tables and querying the analytical metrics. *(Note: Data Viewer inherently includes the `bigquery.tables.list` scope required by the MCP `list_table_ids` tool).*
- **BigQuery Job User** (`roles/bigquery.jobUser`): Grants the agent the fundamental execution authority to compute SQL queries against your billing project footprint.
- **BigQuery Metadata Viewer** (`roles/bigquery.metadataViewer`): Safely provides explicit clearance to iterate and inspect dataset structures directly without hitting access blocks.

**Quick SA Setup:**
If you have just created a new Service Account (`TARGET_SA_EMAIL`) for the ADK agent, run these exact commands from your terminal to attach the required permissions:

```bash
# Set your variables
export PROJECT_ID="your-gcp-project-id"
export ADK_SA="your-sa-name@$PROJECT_ID.iam.gserviceaccount.com"

# Grant the roles
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
```

---

## Setup & Installation

### 1. Configure the Environment
Copy the configuration template and fill it with your Google Cloud project details.

```bash
cp .env_template .env
```
Inside `.env`, define your active `PROJECT_ID`, location config, engine info, and destination dataset specifications.

### 2. Install Python Dependencies
You must install the project's required libraries. If you are using standard `pip`:
```bash
pip install -r requirements.txt
```
*Alternatively, you can use `uv` for a significantly faster, drop-in replacement resolver: `uv pip install -r requirements.txt`.*

### 3. BigQuery Provisioning
Execute the startup script to create the necessary dataset (`gemini_analytics`) and the base metrics table within your GCP infrastructure according to your project configurations.
```bash
./start.sh
```

---

## Data Ingestion Steps

The extraction requires running several targeted scripts to populate the 3 base tables:

1. **`python metrics_to_bq.py`**
   - Fires an asynchronous job pushing the raw Google Cloud Analytics metrics to the `monthly_leaderboard` table.
2. **`python fetch_agent_names.py`**
   - Traverses the entire Discovery Engine `Engine -> Assistant -> Agent` hierarchy via the `v1alpha` API. Extracts exact agent display names and maps them within the `agent_names` table.
3. **Historical Setup via `export_historical_creators.sh`**
   - Scans 365 days of Cloud Audit Logs for previous `CreateAgent` events, parses the caller's principal email with `jq`, and safely backfills the `historical_creators` table.
4. **Live Logging via `setup_sink.sh`**
   - Creates a live Google Cloud Logging Sink to automatically stream all *future* agent creations directly into BigQuery without requiring any manual polling.

### Operational Cadence (Scheduling)
Depending on your operational requirements, metrics extraction should not be purely manual. 
**Recommendation:** Deploy `metrics_to_bq.py` and `fetch_agent_names.py` to **Google Cloud Run Jobs** and trigger them nightly (or weekly) via **Google Cloud Scheduler**. The `setup_sink.sh` ensures agent creation events are streamed in real-time natively, so no scheduling is required for creators.

---

## Local Analytics Agent (ADK)

This repository includes a powerful, pre-configured **Vertex AI Agent** built specifically with the Agent Development Kit (ADK) capable of chatting with this BigQuery data natively using MCP!

### The Vision: Empowering Change Management
Imagine deploying this ADK agent to **Vertex AI Agent Engine** and sharing its natural-language conversational interface directly with your Change Management, Platform Adoption, or Executive teams. Instead of manually writing SQL queries or building complex dashboards, non-technical stakeholders can simply ask the agent about specific data insights.

![ADK Agent Demo](./images/adk_agent_demo.png)


### Running the Agent
For detailed instructions on configuring the environment, installing dependencies, and testing this ADK agent locally, refer to the [documentation](./adk_agent/README.md).
