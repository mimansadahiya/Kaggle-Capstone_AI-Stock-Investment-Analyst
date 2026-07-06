import os
import asyncio
from google import genai
from google.genai import types

def generate_industry_analysis_sync(ticker_or_name: str) -> str:
    """
    Synchronously runs Agent 3 analysis using Google GenAI SDK with Search Grounding.
    """
    # Initialize the client. It will automatically load the GEMINI_API_KEY from environment variables.
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable is not set. Please set it in your environment or .env file."
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are Agent 3, a Senior Industry & Market Research Analyst in Equity Research.
Your task is to provide a comprehensive, investment-banking-grade Industry and Market Analysis for the sector/market of the following company or ticker: {ticker_or_name}.

Please research the most up-to-date and accurate industry metrics using Google Search. Your report must contain the following sections:

1. **Market Size & Historical Growth**:
   - Total Addressable Market (TAM) or overall global industry size (in USD value) for the company's core markets.
   - Historical growth trends of the market over the past 3-5 years.

2. **Projected Market Growth & CAGR**:
   - Projected market size and expected compound annual growth rate (CAGR) for the next 5-10 years (e.g., from 2026 to 2031/2036).
   - Show projections/estimates in a markdown table where appropriate.

3. **Key Industry Trends & Growth Drivers**:
   - Major secular trends currently shaping the industry.
   - Core drivers of growth (e.g., technological paradigm shifts, changing consumer behavior, demographics, rising demand).

4. **Key Challenges & Headwinds**:
   - Current and emerging challenges facing the industry (e.g., regulatory pressure, supply chain vulnerabilities, rising material/labor costs, macroeconomic shifts, security concerns).

5. **Competitive Landscape & Dynamics**:
   - Competitor mapping: identify main competitors and estimate their market shares.
   - Barriers to entry (e.g., capital scale, patents, network effects, high customer switching costs).

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
        return f"Error executing Agent 3 (Industry Analysis): {str(e)}"

async def get_industry_analysis(ticker_or_name: str) -> str:
    """
    Asynchronously runs the synchronous Agent 3 analysis in a thread pool.
    """
    return await asyncio.to_thread(generate_industry_analysis_sync, ticker_or_name)
