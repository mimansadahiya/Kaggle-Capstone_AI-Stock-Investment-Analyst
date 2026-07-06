import os
import asyncio
from dotenv import load_dotenv

# Set PYTHONPATH helper to allow import from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator import run_analysis

# Load .env file
load_dotenv()

async def main():
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = input("Enter a stock ticker or company name to test (e.g. AAPL, NVDA): ").strip()
    if not ticker:
        ticker = "AAPL"
        
    print(f"\n--- Starting CLI Test for '{ticker}' ---")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found in environment or .env file.")
        print("Please configure GEMINI_API_KEY in backend/.env to run the analysis.")
        return

    async for event in run_analysis(ticker):
        event_type = event.get("type")
        agent = event.get("agent", "System")
        message = event.get("message", "")
        
        if event_type == "log":
            print(f"[{agent}] {message}")
        elif event_type == "report":
            print(f"\n=================== REPORT FROM {agent.upper()} ===================")
            print(message[:500] + "\n... (truncated for preview) ...\n")
            print(f"===============================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
