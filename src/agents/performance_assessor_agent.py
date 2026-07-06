import os
import time
import urllib.request
import urllib.parse
import requests
from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

AGENT_INSTRUCTIONS = """You are a senior equity research analyst specializing in financial and operational performance assessment of publicly listed companies.

Analyze the provided search results context and construct an institutional-grade financial and operational performance report for the requested company.

IMPORTANT: This is a performance-analysis engine, not a full investment memo. Do not provide any valuations, investment theses, or buy/hold/sell recommendations.

### Non-Negotiable Operating Principles:
1. Primary sources first: Prefer official Annual Reports, 10-Ks, 20-Fs, quarterly filings, earnings call transcripts, and investor presentations found in the search context.
2. Zero fabrication: Never invent any numbers, dates, ratios, quotes, or citations. If a figure is not in the context or cannot be verified, explicitly output "n/a — not disclosed" or "n/a — not found".
3. Cite every number: Include inline source tags on each reported figure: `[Src: <document>, FY/Qtr, p.XX]` or similar referencing the URLs or documents from the search results.
4. Public information only: Never use or guess material non-public information (MNPI).
5. Currency, fiscal-year & scale discipline: State reporting currency, FY-end convention, and unit scale (mn/bn/crore) up front and be consistent.
6. Reported vs. calculated vs. estimated: Label each figure as `[Reported]`, `[Calculated by analyst]`, or `[Consensus/Analyst estimate]`.
7. Restatements & one-offs: Flag restatements, accounting standard changes, or exceptional items.
8. Recency: State the "as-of" date of every dataset and flag stale filings.
9. Visible uncertainty: Use ranges instead of false precision where appropriate.

### Output Structure:
You MUST output your response in JSON format matching this exact schema:
{{
  "sections": [
    {{
      "section_name": "Identity & Performance Summary",
      "summary": "1-2 sentence overall summary",
      "details": "Legal name | Ticker:Exchange | FY-end <MMM> | Currency <CCY> | Sector/Industry | Report as-of date. Performance Summary: One tight paragraph summarizing financial & operational health and trajectory; followed by 3 bullet points: (a) what's improving, (b) what's deteriorating, (c) what's uncertain."
    }},
    {{
      "section_name": "Financial Performance Analysis (3-yr)",
      "summary": "1-2 sentence overall summary",
      "details": "Clean summary table of 3 FYs (+ latest 2 Qs if useful), ratio dashboard with trajectory arrows & drivers, and detailed narrative. Compute growth, margins, returns, leverage & coverage, liquidity, cash metrics, and efficiency metrics from the data."
    }},
    {{
      "section_name": "Operational Performance Analysis (3-yr)",
      "summary": "1-2 sentence overall summary",
      "details": "Sector KPI table with trajectory, and narrative. Attribute direct quotes (max 15 words). Detect the sector and track appropriate KPIs (e.g. SaaS: ARR/NRR; Retail: SSSG; Banking: CASA/NPA; IT Services: utilization, etc.)."
    }},
    {{
      "section_name": "Benchmarking vs. Peers & Industry",
      "summary": "1-2 sentence overall summary",
      "details": "Quantitative comparison table comparing the company vs. 3-5 named peers and industry average (with sources). State whether the company leads, is in-line, or lags, quantifying the gap."
    }},
    {{
      "section_name": "Source Log & Data Gaps",
      "summary": "1-2 sentence overall summary",
      "details": "A mandatory Source Log table containing document details and a list of any data gaps (n/a) and their impact."
    }}
  ]
}}
"""

class PerformanceAssessorAgent:
    """
    Sub-agent responsible for conducting a senior equity research financial/operational
    performance assessment using custom DuckDuckGo Lite search scraping and Gemini LLM.
    """
    def __init__(self):
        # Fallback environment key loading
        self.default_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def retrieve_search_context(self, company_name: str) -> str:
        """
        Retrieves search context for the company by performing queries via DuckDuckGo Lite.
        """
        queries = [
            f"{company_name} primary listing legal name ticker exchange ISIN FY-end reporting currency",
            f"{company_name} 10-K annual report FY 2024 FY 2023 3 year financial statements revenue net income",
            f"{company_name} earnings call transcript Q4 Q3 2025 2026 investor presentation operational KPIs",
            f"{company_name} competitors peers benchmarking industry average gross margin debt equity"
        ]
        
        context_parts = []
        context_parts.append(f"Target Entity: {company_name}\n")
        
        for q in queries:
            url = 'https://lite.duckduckgo.com/lite/'
            data = urllib.parse.urlencode({'q': q}).encode('utf-8')
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    html = response.read()
                    soup = BeautifulSoup(html, 'html.parser')
                    links = soup.find_all('a', class_='result-link')
                    snippets = soup.find_all('td', class_='result-snippet')
                    
                    context_parts.append(f"### Search Results for: {q}")
                    for i in range(min(5, len(links), len(snippets))):
                        context_parts.append(
                            f"Title: {links[i].text.strip()}\n"
                            f"URL: {links[i]['href']}\n"
                            f"Snippet: {snippets[i].text.strip()}\n"
                            f"---"
                        )
                    context_parts.append("\n")
                time.sleep(1)
            except Exception as e:
                context_parts.append(f"Failed query '{q}': {e}\n")
                
        return "\n".join(context_parts)

    def analyze_performance(
        self,
        api_key: Optional[str],
        company_name: str
    ) -> str:
        """
        Gathers search results and analyzes them via Gemini LLM using REST API.
        """
        active_key = api_key or self.default_api_key

        if not active_key:
            return """> [!WARNING]
> **Gemini API Key Missing**: A valid Gemini API Key is required to perform Performance Assessment analysis. Please configure your key in the sidebar.
"""

        # Perform search scraping
        context = self.retrieve_search_context(company_name)

        prompt = f"""{AGENT_INSTRUCTIONS}

Search Context Data:
{context}

Target Company: {company_name}
"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={active_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
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
> * **Temporary Delay**: Please wait 1-2 minutes and toggle this agent ON again to retry.
"""
            else:
                return f"""> [!ERROR]
> **Gemini API Request Failed (Status {response.status_code})**: Unable to complete performance assessment.
> Details: {response.text}
"""
        except Exception as e:
            return f"""> [!ERROR]
> **Connection Error**: Failed to request Gemini API.
> Details: {e}
"""
