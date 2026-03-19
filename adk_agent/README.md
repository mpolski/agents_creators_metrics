# Local Analytics Agent (ADK)

This directory contains a pre-configured **Vertex AI Agent** built specifically with the Agent Development Kit (ADK) to chat naturally with your enriched BigQuery metrics using the native BigQuery MCP server.

## Testing the Agent Locally

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
4. **Spin up the Web Client:**
   Run the local ADK interface to start chatting:
   ```bash
   adk web adk_agent
   ```
   *(Alternatively, you can test the raw execution via `python adk_agent/run_local_test.py`)*
