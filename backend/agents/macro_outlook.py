import os
import asyncio
from google import genai
from google.genai import types

def generate_macro_outlook_sync(ticker_or_name: str) -> str:
    """
    Synchronously runs Agent 2 analysis using Google GenAI SDK with Search Grounding.
    """
    # Initialize the client. It will automatically load the GEMINI_API_KEY from environment variables.
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable is not set. Please set it in your environment or .env file."
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are Agent 2, a Senior Macroeconomic and Sector Strategist in Equity Research.
Your task is to provide a comprehensive, investment-banking-grade Macroeconomic Status and Sector Outlook for the following company or ticker: {ticker_or_name}.

Please research the most up-to-date macroeconomic indices and industry data using Google Search. Your report must contain the following sections:

1. **Macroeconomic Environment**:
   - Current macroeconomic climate (interest rates, inflation rates/CPI/PCE, GDP growth trends) in the primary countries of operation for this company.
   - Analysis of how these broad economic factors impact the company's cost of capital and consumer demand.

2. **Sector & Industry Trends**:
   - Current state of the company's primary industry (growth cycles, market dynamics, supply chain issues, or commodity price fluctuations).
   - Major headwind and tailwind trends currently shaping the industry.

3. **Economic Measures & Policy Impacts**:
   - Impact of central bank actions (monetary policies, interest rate hikes/cuts).
   - Impact of fiscal policies, government spending, tariffs, trade policies, and specific regulatory shifts (e.g., green policies, technology controls, labor regulations) affecting the company or its sector.

4. **Macro-driven Risks & Opportunities**:
   - Synthesis of macro-driven risks (e.g., foreign exchange risks, inflation margin pressure, pricing power erosion).
   - Macro-driven opportunities (e.g., government subsidies, demographic shifts, defensive market position).

Format the output in elegant, professional markdown. Use bold highlights, clear headers, bullet points, and markdown tables. Make it read like a premium equity research report.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        # Check if we got a valid response
        if response.text:
            return response.text
        else:
            return "Error: Received empty response from Gemini API."
    except Exception as e:
        return f"Error executing Agent 2 (Macro Outlook): {str(e)}"

async def get_macro_outlook(ticker_or_name: str) -> str:
    """
    Asynchronously runs the synchronous Agent 2 analysis in a thread pool.
    """
    return await asyncio.to_thread(generate_macro_outlook_sync, ticker_or_name)
