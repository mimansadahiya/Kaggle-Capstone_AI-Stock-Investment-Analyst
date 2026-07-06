import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Ensure app is in path
sys.path.append(".")

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

def main():
    stock_query = "Tesla, Inc."
    if len(sys.argv) > 1:
        stock_query = sys.argv[1]
        
    print(f"Initializing direct agent run for stock: {stock_query}...", flush=True)
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text=f"Please perform a valuation analysis for {stock_query}")]
    )

    print("Running agent (fetching yfinance data + web search & constructing valuation)...", flush=True)
    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    print("\n--- Agent Output ---\n", flush=True)
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print("\n\n--------------------", flush=True)

if __name__ == "__main__":
    main()
