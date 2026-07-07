import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class MacroOutlookAgent:
    """
    Sub-agent responsible for conducting a comprehensive Macroeconomic Environment
    and Sector Outlook analysis using Google Search Grounded Gemini LLM queries.
    """
    def __init__(self):
        # Fallback environment key loading
        self.default_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def analyze_macro_outlook(
        self,
        api_key: Optional[str],
        company_name: str,
        ticker: str,
        sector: str,
        industry: str
    ) -> str:
        """
        Retrieves grounded macroeconomic and industry sector status analysis via Gemini API with Google Search.
        """
        active_key = api_key or self.default_api_key

        if not active_key:
            return """> [!WARNING]
> **Gemini API Key Missing**: A valid Gemini API Key is required to perform real-time web-grounded Macro Outlook analysis. Please configure your key in the sidebar.
"""

        prompt = f"""
You are Agent 2, a Senior Macroeconomic and Sector Strategist in Equity Research.
Your task is to provide a comprehensive, investment-banking-grade Macroeconomic Status and Sector Outlook for the following company: {company_name} (Ticker: {ticker}) in the {sector} / {industry} industry.

You MUST structure your response into 4 sections:
1. Macroeconomic Environment
2. Sector & Industry Trends
3. Economic Measures & Policy Impacts
4. Macro-driven Risks & Opportunities

Analyze the following for each section:
1. **Macroeconomic Environment**: Current macroeconomic climate (interest rates, inflation rates/CPI/PCE, GDP growth trends) in the primary countries of operation for this company. Analysis of how these broad economic factors impact the company's cost of capital and consumer demand.
2. **Sector & Industry Trends**: Current state of the company's primary industry (growth cycles, market dynamics, supply chain issues, or commodity price fluctuations). Major headwind and tailwind trends currently shaping the industry.
3. **Economic Measures & Policy Impacts**: Impact of central bank actions (monetary policies, interest rate hikes/cuts), fiscal policies, government spending, tariffs, trade policies, and specific regulatory shifts (e.g., green policies, technology controls, labor regulations) affecting the company or its sector.
4. **Macro-driven Risks & Opportunities**: Synthesis of macro-driven risks (e.g., foreign exchange risks, inflation margin pressure, pricing power erosion) and opportunities (e.g., government subsidies, demographic shifts, defensive market position).

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
> **Gemini API Request Failed (Status {response.status_code})**: Unable to complete macro outlook analysis.
> Details: {response.text}
"""
        except Exception as e:
            return f"""> [!ERROR]
> **Connection Error**: Failed to request Gemini API.
> Details: {e}
"""
