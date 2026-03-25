import os
import requests
from google.auth import default
from google.auth.transport.requests import Request
from google.cloud import bigquery
from dotenv import load_dotenv

# 1. Load variables from .env
load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("GE_LOCATION", "global")
DATASET_ID = os.getenv("DATASET_ID")

# 2. Get Authentication Token
print("🔑 Getting Google Cloud credentials...")
credentials, _ = default()
credentials.refresh(Request())
TOKEN = credentials.token

# 3. Fetch Agents (Engines) from the API
url = f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "x-goog-user-project": PROJECT_ID
}

print(f"🔍 Fetching Agent Names from Vertex AI...")
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code} - {response.text}")
    exit(1)

engines = response.json().get("engines", [])

if not engines:
    print("⚠️ No agents found in this project/location.")
    exit(0)

# 4. Fetch Assistants and Agents for each Engine
records = []
for engine in engines:
    engine_name = engine.get("name")
    if not engine_name:
        continue
        
    # A. Fetch Engine DataStores
    engine_details_url = f"https://discoveryengine.googleapis.com/v1/{engine_name}"
    eng_res = requests.get(engine_details_url, headers=headers)
    datastore_ids_str = ""
    datastore_names_str = ""
    
    if eng_res.status_code == 200:
        eng_data = eng_res.json()
        data_store_ids = eng_data.get("dataStoreIds", [])
        datastore_ids_str = ",".join(data_store_ids)
        
        # B. Fetch DataStore Names (Optional but preferred)
        ds_names = []
        for ds_id in data_store_ids:
            ds_url = f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{ds_id}"
            ds_res = requests.get(ds_url, headers=headers)
            if ds_res.status_code == 200:
                ds_names.append(ds_res.json().get("displayName", ds_id))
            else:
                ds_names.append(ds_id)
        datastore_names_str = ",".join(ds_names)

    # Fetch Assistants
    assistants_url = f"https://discoveryengine.googleapis.com/v1alpha/{engine_name}/assistants"
    ast_res = requests.get(assistants_url, headers=headers)
    if ast_res.status_code != 200:
        continue
        
    assistants = ast_res.json().get("assistants", [])
    for ast in assistants:
        ast_name = ast.get("name")
        if not ast_name:
            continue
            
        # Fetch Agents
        agents_url = f"https://discoveryengine.googleapis.com/v1alpha/{ast_name}/agents"
        agt_res = requests.get(agents_url, headers=headers)
        if agt_res.status_code != 200:
            continue
            
        agents = agt_res.json().get("agents", [])
        for agt in agents:
            raw_agt_name = agt.get("name", "")
            if not raw_agt_name:
                continue
            agent_id = raw_agt_name.split("/")[-1]
            display_name = agt.get("displayName", "Unknown")
            
            # C. Fetch Agent Details (Specific Endpoint)
            agt_details_url = f"https://discoveryengine.googleapis.com/v1alpha/{raw_agt_name}"
            agt_det_res = requests.get(agt_details_url, headers=headers)
            
            description_string = ""
            system_instructions_string = ""
            
            if agt_det_res.status_code == 200:
                agt_data = agt_det_res.json()
                description_string = agt_data.get("description", "")
                
                # ADK Agent or Agent Builder UI categorization
                agent_type = "Unknown"
                if "adkAgentDefinition" in agt_data:
                    agent_type = "ADK Agent"
                elif "agentBuilderDefinition" in agt_data:
                    agent_type = "Agent Builder (UI)"
                    builder_def = agt_data["agentBuilderDefinition"]
                    agents_list = builder_def.get("draftAgents", builder_def.get("agents", []))
                    root_id = builder_def.get("deployedRootAgentId", builder_def.get("draftRootAgentId", "root_agent"))
                    
                    sub_instructions = []
                    for a in agents_list:
                        node = a.get("llmAgentNode", {})
                        inst = node.get("instruction", "")
                        if inst:
                            if a.get("id") == root_id:
                                system_instructions_string = inst + "\n\n" + system_instructions_string
                            else:
                                sub_instructions.append(f"[{a.get('displayName', 'Sub-Agent')}] {inst}")
                    
                    if sub_instructions:
                        system_instructions_string += "Sub-Agent Instructions:\n" + "\n".join(sub_instructions)

                # Fallback for standard/older single-prompt agents
                prompt_data = agt_data.get("prompt", {})
                if not system_instructions_string:
                    system_instructions_string = prompt_data.get("systemInstruction", agt_data.get("systemInstruction", ""))
            
            # D. Update the Data Record
            records.append({
                "agent_id": agent_id,
                "display_name": display_name,
                "description": description_string,
                "system_instructions": system_instructions_string.strip(),
                "datastore_ids": datastore_ids_str,
                "datastore_names": datastore_names_str,
                "agent_type": agent_type
            })

print(f"✅ Found {len(records)} agents. Pushing to BigQuery...")

# 5. Push to BigQuery (Overwriting the table so it is always perfectly synced)
client = bigquery.Client(project=PROJECT_ID)
table_ref = f"{PROJECT_ID}.{DATASET_ID}.agent_names"

job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_TRUNCATE", # This replaces the table data
    autodetect=True,
    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
)

job = client.load_table_from_json(records, table_ref, job_config=job_config)
job.result() 

print(f"🎉 Success! Agent names mapped and saved to {table_ref}")