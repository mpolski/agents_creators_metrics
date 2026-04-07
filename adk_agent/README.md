# Local Analytics Agent (ADK)

This directory contains a pre-configured **Vertex AI Agent** built specifically with the Agent Development Kit (ADK) to chat naturally with your enriched BigQuery metrics using the native BigQuery MCP server.

This guide offers two options for testing and deploying the agent:
* [Option 1: Testing the Agent with ADK web locally](#option-1-testing-the-agent-with-adk-web-locally)
* [Option 2: Using Agent Starter Pack for testing locally and Deploying to Agent Engine](#option-2-using-agent-starter-pack-for-testing-locally-and-deploying-to-agent-engine)

## ADK Prerequisites
Before running this agent, you must have the **Agent Development Kit (ADK)** installed. 
While this project's `requirements.txt` installs it automatically into your environment, you can also install the ADK globally via:
```bash
pip install google-adk
```
For more detailed installation instructions, configuration management, and deployment guides, please refer to the [official ADK GitHub page](https://github.com/google/google-adk-python).

## 1. Enable BigQuery MCP
You must explicitly enable the native BigQuery MCP service on your project infrastructure so the agent can discover BigQuery tools:
```bash
gcloud beta services mcp enable bigquery.googleapis.com --project="your-gcp-project-id"
```

## 2. ADK Agent Service Account & IAM
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

## Option 1. Testing the Agent with ADK web locally

1. **Navigate to the parent directory:**
   ```bash
   cd ..
   ```
2. **Install the dependencies:**
   ```bash
   pip install -r adk_agent/requirements.txt
   ```
3. **Configure Environment:**
   Ensure your `adk_agent/.env` file is properly configured with your `TARGET_SA_EMAIL` and `DATA_PROJECT_ID`.

4. **Authenticate with Google Cloud:**
   Run the application-default login to allow impersonation:
   ```bash
   gcloud auth application-default login
   ```

5. **Spin up the Web Client:**
   Run the local ADK interface to start chatting:
   ```bash
   adk web adk_agent
   ```
   *(Alternatively, you can test the raw execution via `python adk_agent/run_local_test.py`)*

## Option 2. Using Agent Starter Pack for testing locally and Deploying to Agent Engine

If you prefer to use the **Agent Starter Pack**, follow these simplified steps to test locally and deploy to Agent Engine.

1. **Prerequisites**: Refer to the [Agent Starter Pack documentation](https://googlecloudplatform.github.io/agent-starter-pack/guide/getting-started.html) for installation instructions.

2. **Enhance the Agent**:
   ```bash
   uvx agent-starter-pack enhance
   ```

3. **Test Locally**:
   ```bash
   make install
   make playground
   ```

4. **Prepare for Deployment**:
   Copy the example environment file and update it with your settings:
   ```bash
   cp .env.example .env
   ```

5. **Deploy**:
   ```bash
   make deploy
   ```

Upon a successful deployment, you will see an output similar to the following. You can follow the link to the Playground to test the deployed agent from the Agent Engine:

```
✅ Deployment successful!
Service Account: service-<PROJECT_NUMBER>@gcp-sa-aiplatform-re.iam.gserviceaccount.com

📊 Open Console Playground: https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/<AGENT_ID>/playground?project=<PROJECT_ID>
```
