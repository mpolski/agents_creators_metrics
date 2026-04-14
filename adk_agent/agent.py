# agent.py
import os
from dotenv import load_dotenv

# Load environment variables from the same directory as this file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials  # <--- NEW MODULE
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams

# Import the prompt
try:
    from . import prompt
except ImportError:
    import prompt

# --- CONFIGURATION ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
MCP_ENDPOINT = os.environ.get("MCP_ENDPOINT")
# The Service Account Email
TARGET_SA_EMAIL = os.environ.get("TARGET_SA_EMAIL")

current_project = os.environ.get("GOOGLE_CLOUD_PROJECT")

# Ensure critical variables are set
if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
if not LOCATION:
    raise ValueError("GOOGLE_CLOUD_LOCATION environment variable is not set")
if not MCP_ENDPOINT: # Default to current used if not provided? No, explicit is better
    raise ValueError("MCP_ENDPOINT environment variable is not set")
if not TARGET_SA_EMAIL:
   raise ValueError("TARGET_SA_EMAIL environment variable is not set")

# Set Env Vars (if not already set, but we just read them so they should be)
# os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID # Redundant if read from env
# os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION # Redundant
# os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = PROJECT_ID # Good practice to ensure quota project is set
if "GOOGLE_CLOUD_QUOTA_PROJECT" not in os.environ:
    os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = PROJECT_ID

# --- 1. AUTHENTICATION (IMPERSONATION) ---
print(f"Authenticating as {TARGET_SA_EMAIL} (via Impersonation)...")

# A. Get your generic User Credentials (source)
source_creds, _ = google.auth.default()

# B. Create Impersonated Credentials
# This tells Google: "I am Bruce, but I want to act as the Service Account"
target_creds = impersonated_credentials.Credentials(
    source_credentials=source_creds,
    target_principal=TARGET_SA_EMAIL,
    target_scopes=["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/bigquery"],
    lifetime=3600
)

# C. Refresh to generate the actual Access Token for the Service Account
auth_req = google.auth.transport.requests.Request()
target_creds.refresh(auth_req)
access_token = target_creds.token

# D. Define headers using the SA's token
connection_headers = {
    "Authorization": f"Bearer {access_token}",
    "x-goog-user-project": PROJECT_ID,
    "Content-Type": "application/json"
}

# --- 2. DIRECT CONNECTION ---
print(f"Connecting to MCP Endpoint: {MCP_ENDPOINT}")

mcp_connection_params = StreamableHTTPConnectionParams(
    url=MCP_ENDPOINT,
    headers=connection_headers
)

try:
    database_tools = MCPToolset(connection_params=mcp_connection_params)
    print("Successfully initialized direct BigQuery MCP connection.")
except Exception as e:
    print(f"Error initializing toolset: {e}")
    raise e

# --- 3. AGENT DEFINITION ---
root_agent = LlmAgent(
    name="agents_creator_metrics",
    model=os.environ.get("MODEL_NAME", "gemini-2.5-flash"),
    instruction=prompt.PROMPT,
    description="An agent that queries Gemini Analytics metrics using a BigQuery MCP server.",
    tools=[database_tools]
)

from google.adk.apps import App

app = App(root_agent=root_agent, name="adk_agent")
