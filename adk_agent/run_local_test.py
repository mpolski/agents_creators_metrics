
from google.adk.runners import InMemoryRunner
from google.genai import types
from agent import root_agent
import logging
import vertexai

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("google_adk").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GCP Project Details
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")

if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
if not LOCATION:
    raise ValueError("GOOGLE_CLOUD_LOCATION environment variable is not set")

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION

import asyncio

async def main():
    print("Initializing Vertex AI...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("Initializing InMemoryRunner...")
    runner = InMemoryRunner(agent=root_agent)
    
    user_id = "test_user"
    session_id = "test_session"
    prompt = "show me the list of agents and their owners"
    
    print(f"Sending query: {prompt}")
    
    # Create session
    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id
    )

    # Run asynchronously
    try:
        print("\n--- Agent Response Events ---")
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role='user', parts=[types.Part(text=prompt)])
        ):
            # Event object has .content and .author
            if event.author == 'agents_creator_metrics' and event.content:
                print(f"Agent: {event.content}")
            else:
                print(f"Event: {event}")
        print("\n-----------------------------")
    finally:
        print("Closing resources...")
        # Close database_tools explicitly
        from agent import database_tools
        import inspect
        
        if hasattr(database_tools, 'close'):
            if inspect.iscoroutinefunction(database_tools.close):
                await database_tools.close()
            else:
                database_tools.close()
                
        # Close runner
        if hasattr(runner, 'close'):
            if inspect.iscoroutinefunction(runner.close):
                await runner.close()
            else:
                runner.close()

if __name__ == "__main__":
    asyncio.run(main())
