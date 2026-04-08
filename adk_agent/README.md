# Local Analytics Agent (ADK) - Deployment

This guide describes how to test locally and deploy the agent to **Vertex AI Agent Engine** using the **Agent Starter Pack**.

## Using Agent Starter Pack for testing locally and Deploying to Agent Engine

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
