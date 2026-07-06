import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class CompanyOverviewAgent:
    """
    Sub-agent responsible for conducting a comprehensive Company Overview analysis
    using Google Search Grounded Gemini LLM queries.
    """
    def __init__(self):
        # Fallback environment key loading
        self.default_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def analyze_company_overview(
        self,
        api_key: Optional[str],
        company_name: str,
        ticker: str,
        sector: str,
        industry: str
    ) -> str:
        """
        Retrieves grounded company overview analysis via Gemini API with Google Search.
        """
        active_key = api_key or self.default_api_key

        if not active_key:
            return """> [!WARNING]
> **Gemini API Key Missing**: A valid Gemini API Key is required to perform real-time web-grounded Company Overview analysis. Please configure your key in the sidebar.
"""

        prompt = f"""
You are Agent 1, a Senior Investment Banking Research Analyst specializing in equity research. 
Your task is to provide a comprehensive, investment-banking-grade Company Overview for the following company: {company_name} (Ticker: {ticker}) in the {sector} / {industry} industry.

You MUST structure your response into 4 sections:
1. Executive Summary & Corporate Info
2. Business Model & Value Proposition
3. Business Lines & Revenue Segments
4. Corporate Strategy & Future Pipelines

Analyze the following for each section:
1. **Executive Summary & Corporate Info**: Official name, ticker, sector, industry, headquarters, key executives (CEO, CFO, etc.), and a brief summary of the company's core mission and historical context.
2. **Business Model & Value Proposition**: Detailed explanation of how the company generates revenue and its core value proposition, target customer segments, and distribution channels.
3. **Business Lines & Revenue Segments**: Breakdown of major business divisions or product/service lines. If available, include a breakdown of revenue share or growth rates by segment and geographic region (present this in a markdown table).
4. **Corporate Strategy & Future Pipelines**: Critical growth drivers, recent strategic shifts, mergers & acquisitions (M&A), partnerships, current R&D focus, new product/service launches, and technological innovations the company is prioritizing.

You MUST output your response in JSON format matching this exact schema:
{{
  "sections": [
    {{
      "section_name": "Section Name",
      "summary": "A concise, 1-2 sentence overall summary/headline of the section",
      "details": "Detailed, institutional-grade, verbose markdown analysis with bullet points, tables, and paragraphs containing the deep research"
    }}
  ]
}}
"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={active_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "tools": [
                    {"google_search": {}}
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            elif response.status_code == 429:
                return """> [!WARNING]
> **Gemini API Limit Reached (Status 429)**: You have exceeded the request quota limit for the Gemini Free Tier.
> 
> * **Temporary Delay**: The Free Tier limits requests per minute. Please wait 1-2 minutes and toggle this agent ON again to retry.
"""
            else:
                return f"""> [!ERROR]
> **Gemini API Request Failed (Status {response.status_code})**: Unable to complete company overview analysis.
> Details: {response.text}
"""
        except Exception as e:
            return f"""> [!ERROR]
> **Connection Error**: Failed to request Gemini API.
> Details: {e}
"""
