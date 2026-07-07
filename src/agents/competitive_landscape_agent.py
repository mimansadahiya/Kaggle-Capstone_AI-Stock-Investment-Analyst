import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class CompetitiveLandscapeAgent:
    """
    Sub-agent responsible for analyzing the competitive landscape of a company
    using Google Search Grounded Gemini LLM queries.
    """
    def __init__(self):
        # Fallback environment key loading
        self.default_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def analyze_competitive_landscape(
        self,
        api_key: Optional[str],
        company_name: str,
        ticker: str,
        sector: str,
        industry: str
    ) -> str:
        """
        Retrieves grounded competitive landscape analysis via Gemini API with Google Search.
        """
        active_key = api_key or self.default_api_key

        if not active_key:
            return """> [!WARNING]
> **Gemini API Key Missing**: A valid Gemini API Key is required to perform real-time web-grounded Competitive Landscape analysis. Please configure your key in the sidebar.
"""

        prompt = f"""
You are an expert, institutional-grade financial analyst writing an investment memo.
Perform a detailed, web-grounded competitive landscape analysis for {company_name} (Ticker: {ticker}) in the {sector} / {industry} industry.

You MUST structure your response into 4 sections:
1. Key Competitors
2. Market Share & Moat
3. Competitor Updates
4. Barriers to Entry

Analyze the following for each section:
1. **Key Competitors**: Identify the main competitors in the market (both direct and indirect). Highlight their ticker symbols if public.
2. **Market Share & Moat**: Analyze the company's estimated market share compared to these peers. Explain what constitutes the company's sustainable competitive advantage (economic moat) or lack thereof.
3. **Competitor Updates**: Search for the latest major news and developments from key competitors (e.g., newly developed capabilities, new products/services, market expansions, strategic shifts). Explain what these updates mean for {company_name}.
4. **Barriers to Entry**: Evaluate the barriers to entry in this market. Highlight any notable new entrants or substitution threats.

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
                    "responseMimeType": "application/json",
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
> **Gemini API Request Failed (Status {response.status_code})**: Unable to complete competitive landscape analysis.
> Details: {response.text}
"""
        except Exception as e:
            return f"""> [!ERROR]
> **Connection Error**: Failed to request Gemini API.
> Details: {e}
"""
