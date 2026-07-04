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

Your response must be a detailed investment memo section addressing:
1. **Key Competitors**: Identify the main competitors in the market (both direct and indirect). Highlight their ticker symbols if public.
2. **Market Share & Sustainable Advantage (Moat)**: Analyze the company's estimated market share compared to these peers. Explain what constitutes the company's sustainable competitive advantage (economic moat) or lack thereof.
3. **Latest Major Competitor Updates**: Search for the latest major news and developments from key competitors (e.g., newly developed capabilities, new products/services, market expansions, strategic shifts). Explain what these updates mean for {company_name}.
4. **Barriers to Entry, New Entrants & Substitutions**: Evaluate the barriers to entry in this market. Highlight any notable new entrants or substitution threats.

Please structure the memo using professional investment banking layout (Markdown format) with clear tables, bullet points, and headers. Do not use generic placeholders.
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
                ]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
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
