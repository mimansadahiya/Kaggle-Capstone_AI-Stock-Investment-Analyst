import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class IndustryAnalysisAgent:
    """
    Sub-agent responsible for conducting a comprehensive Industry and Market Analysis
    using Google Search Grounded Gemini LLM queries.
    """
    def __init__(self):
        # Fallback environment key loading
        self.default_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def analyze_industry(
        self,
        api_key: Optional[str],
        company_name: str,
        ticker: str,
        sector: str,
        industry: str
    ) -> str:
        """
        Retrieves grounded industry and market analysis via Gemini API with Google Search.
        """
        active_key = api_key or self.default_api_key

        if not active_key:
            return """> [!WARNING]
> **Gemini API Key Missing**: A valid Gemini API Key is required to perform real-time web-grounded Industry Analysis. Please configure your key in the sidebar.
"""

        prompt = f"""
You are Agent 5, a Senior Industry & Market Research Analyst in Equity Research.
Your task is to provide a comprehensive, investment-banking-grade Industry and Market Analysis for the sector/market of the following company: {company_name} (Ticker: {ticker}) in the {sector} / {industry} industry.

You MUST structure your response into 5 sections:
1. Market Size & Historical Growth
2. Projected Market Growth & CAGR
3. Key Industry Trends & Growth Drivers
4. Key Challenges & Headwinds
5. Competitive Landscape & Dynamics

Analyze the following for each section:
1. **Market Size & Historical Growth**: Total Addressable Market (TAM) or overall global industry size (in USD value) for the company's core markets. Historical growth trends of the market over the past 3-5 years.
2. **Projected Market Growth & CAGR**: Projected market size and expected compound annual growth rate (CAGR) for the next 5-10 years (e.g., from 2026 to 2031/2036). Show projections/estimates in a markdown table where appropriate.
3. **Key Industry Trends & Growth Drivers**: Major secular trends currently shaping the industry. Core drivers of growth (e.g., technological paradigm shifts, changing consumer behavior, demographics, rising demand).
4. **Key Challenges & Headwinds**: Current and emerging challenges facing the industry (e.g., regulatory pressure, supply chain vulnerabilities, rising material/labor costs, macroeconomic shifts, security concerns).
5. **Competitive Landscape & Dynamics**: Competitor mapping: identify main competitors and estimate their market shares. Barriers to entry (e.g., capital scale, patents, network effects, high customer switching costs).

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

        import json
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={active_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "tools": [
                    {"google_search": {}}
                ],
                "generationConfig": {
                    "maxOutputTokens": 1000
                }
            }
            json_payload = json.dumps(payload)
            headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(json_payload.encode('utf-8')))
            }
            
            import time
            max_retries = 3
            backoff_seconds = 6
            response = None
            for attempt in range(max_retries):
                response = requests.post(url, headers=headers, data=json_payload, timeout=180)
                if response.status_code == 200:
                    break
                elif response.status_code in [429, 503, 504] and attempt < max_retries - 1:
                    time.sleep(backoff_seconds * (attempt + 1))
                else:
                    break
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            elif response.status_code == 429:
                return f"""> [!WARNING]
> **Gemini API Limit Reached (Status 429)**: Rate limit exceeded.
> **Details**: `{response.text}`
"""
            else:
                return f"""> [!ERROR]
> **Gemini API Request Failed (Status {response.status_code})**: Unable to complete industry analysis.
> Details: {response.text}
"""
        except Exception as e:
            return f"""> [!ERROR]
> **Connection Error**: Failed to request Gemini API.
> Details: {e}
"""
