import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class MajorRisksAgent:
    """
    Sub-agent responsible for analyzing strategic, operational, financial,
    and GRC risk factors using Google Search Grounded Gemini API calls.
    """
    def __init__(self):
        self.default_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def analyze_major_risks(
        self,
        api_key: Optional[str],
        company_name: str,
        ticker: str
    ) -> str:
        """
        Retrieves grounded risk assessment analysis via Gemini API with Google Search.
        """
        active_key = api_key or self.default_api_key

        if not active_key:
            return """> [!WARNING]
> **Gemini API Key Missing**: A valid Gemini API Key is required to perform real-time web-grounded Major Risks analysis. Please configure your key in the sidebar.
"""

        prompt = f"""
You are an expert, institutional-grade risk analyst and compliance officer writing an investment memo.
Perform a detailed, web-grounded qualitative risk assessment for {company_name} (Ticker: {ticker}).

You MUST structure your response into 4 sections:
1. Strategic Risks
2. Operational Risks
3. Financial Risks
4. GRC Risks

Analyze the following for each section:
1. **Strategic Risks**: Risks related to the company's business model, industry disruptions, technological changes, competitive position, or failed expansions.
2. **Operational Risks**: Risks relating to supply chain disruptions, system failures, labor relations, cybersecurity, or day-to-day execution issues.
3. **Financial Risks**: Risks concerning debt levels, liquidity, currency fluctuations, interest rate vulnerability, inflation, or credit downgrades.
4. **GRC Risks**: Risks related to legal battles/lawsuits, regulatory changes, environmental liabilities (ESG issues), and governance problems.

You MUST output your response in JSON format matching this exact schema:
{{
  "sections": [
    {{
      "section_name": "Section Name",
      "summary": "A concise, 1-2 sentence overall summary/headline of the section",
      "details": "Detailed, institutional-grade, verbose markdown analysis with bullet points and paragraphs containing the deep research"
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
> **Gemini API Request Failed (Status {response.status_code})**: Unable to complete major risks analysis.
> Details: {response.text}
"""
        except Exception as e:
            return f"""> [!ERROR]
> **Connection Error**: Failed to request Gemini API.
> Details: {e}
"""
