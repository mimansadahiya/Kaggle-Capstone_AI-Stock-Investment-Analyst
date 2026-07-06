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

def run_analysis(company_name: str, output_file: str):
    print(f"Initializing analysis for '{company_name}'...", flush=True)
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text=f"Please perform financial and operational analysis for {company_name}.")]
    )

    print("Running workflow (fetching filings and generating report)...", flush=True)
    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    report_text = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    report_text += part.text

    if not report_text:
        print("Error: No report was generated. Check API configuration.", flush=True)
        return

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print(f"\nSuccess! Report saved to: {output_file}", flush=True)

if __name__ == "__main__":
    company = "Tesla"
    if len(sys.argv) > 1:
        company = sys.argv[1]
    run_analysis(company, f"../{company.lower().replace(' ', '_')}_performance_report.md")
