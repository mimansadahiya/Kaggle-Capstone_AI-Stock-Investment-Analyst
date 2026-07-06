import os
import asyncio
from google import genai
from google.genai import types

def generate_company_overview_sync(ticker_or_name: str) -> str:
    """
    Synchronously runs Agent 1 analysis using Google GenAI SDK with Search Grounding.
    """
    # Initialize the client. It will automatically load the GEMINI_API_KEY from environment variables.
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable is not set. Please set it in your environment or .env file."
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are Agent 1, a Senior Investment Banking Research Analyst specializing in equity research. 
Your task is to provide a comprehensive, investment-banking-grade Company Overview for the following company or ticker: {ticker_or_name}.

Please research the most up-to-date and accurate information using Google Search. Your report must contain the following sections:

1. **Executive Summary & Key Corporate Info**: 
   - Official name, ticker, sector, industry, headquarters, and key executives (CEO, CFO, etc.).
   - A brief summary of the company's core mission and historical context.
   
2. **Business Model & Value Proposition**:
   - Detailed explanation of how the company generates revenue and its core value proposition.
   - Target customer segments and distribution channels.

3. **Business Lines & Revenue Segments**:
   - Breakdown of major business divisions or product/service lines.
   - If available, include a breakdown of revenue share or growth rates by segment and geographic region (present this in a markdown table).

4. **Corporate Strategy & Strategic Initiatives**:
   - Critical growth drivers, recent strategic shifts, mergers & acquisitions (M&A), and partnerships.
   
5. **Key Focus Areas & Future Pipelines**:
   - Current research & development (R&D) focus, new product/service launches, and technological innovations the company is prioritizing.

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
        return f"Error executing Agent 1 (Company Overview): {str(e)}"

async def get_company_overview(ticker_or_name: str) -> str:
    """
    Asynchronously runs the synchronous Agent 1 analysis in a thread pool.
    """
    return await asyncio.to_thread(generate_company_overview_sync, ticker_or_name)
