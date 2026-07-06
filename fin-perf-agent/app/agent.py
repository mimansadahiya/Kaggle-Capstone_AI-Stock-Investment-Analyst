# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
from typing import Any
from google.adk.workflow import Workflow, START, node, Edge
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


@node
def retrieve_stock_data(node_input: Any) -> str:
    """Retrieves stock information, financial filings, transcripts, and peer metrics
    using a hybrid yfinance API lookup and DuckDuckGo Search fallback.
    """
    text = ""
    if hasattr(node_input, 'parts') and node_input.parts:
        text = node_input.parts[0].text
    elif isinstance(node_input, dict) and 'parts' in node_input:
        text = node_input['parts'][0].get('text', '')
    else:
        text = str(node_input)

    import re
    cleaned = text.strip()
    cleaned = re.sub(r'(?i).*?financial and operational performance assessment of\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?financial and operational performance assessment for\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?financial and operational analysis for\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?performance assessment of\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?performance assessment for\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?analysis of\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?analysis for\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?analyze\s+', '', cleaned)
    company_name = cleaned.strip('.').strip()

    import json
    import urllib.request
    import urllib.parse
    import yfinance as yf
    import pandas as pd
    import time
    from bs4 import BeautifulSoup

    context_parts = []
    context_parts.append(f"Target Entity: {company_name}")

    # 1. Resolve Ticker Symbol
    symbol = None
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(company_name)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            quotes = data.get('quotes', [])
            if quotes:
                symbol = quotes[0].get('symbol')
    except Exception as e:
        context_parts.append(f"Ticker lookup error: {e}")

    # Helper to convert DataFrame to Markdown
    def df_to_markdown(df):
        if df is None or df.empty:
            return "n/a — not available"
        df.columns = [str(c)[:10] for c in df.columns]
        df.index = [str(i) for i in df.index]
        headers = ["Metric"] + list(df.columns)
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for idx, row in df.iterrows():
            row_vals = []
            for val in row.values:
                if pd.isna(val):
                    row_vals.append("n/a")
                elif isinstance(val, (int, float)):
                    row_vals.append(f"{val:,.2f}" if val % 1 != 0 else f"{int(val):,}")
                else:
                    row_vals.append(str(val))
            lines.append(f"| {idx} | " + " | ".join(row_vals) + " |")
        return "\n".join(lines)

    # 2. Get target financials
    industry = ""
    if symbol:
        context_parts.append(f"Ticker Symbol: {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            industry = info.get('industry', '')
            context_parts.append(f"Legal Name: {info.get('longName', company_name)}")
            context_parts.append(f"Sector: {info.get('sector', 'n/a')}")
            context_parts.append(f"Industry: {industry}")
            context_parts.append(f"Exchange: {info.get('exchange', 'n/a')}")
            context_parts.append(f"Currency: {info.get('financialCurrency', 'USD')}")

            # Financial Tables
            context_parts.append("\n### Target Company Financial Statements")
            context_parts.append("#### Income Statement:")
            context_parts.append(df_to_markdown(ticker.financials))
            context_parts.append("#### Balance Sheet:")
            context_parts.append(df_to_markdown(ticker.balance_sheet))
            context_parts.append("#### Cash Flow:")
            context_parts.append(df_to_markdown(ticker.cashflow))
        except Exception as e:
            context_parts.append(f"Error fetching target company financials: {e}")
    else:
        context_parts.append(f"Ticker could not be resolved for {company_name}")

    # 3. Retrieve Peer Benchmarking financials
    peer_tickers = []
    if industry:
        # Peer lookup mapping
        industry_map = {
            "Auto Manufacturers": ["F", "GM", "RIVN", "BYDDY"],
            "Consumer Electronics": ["MSFT", "GOOGL", "AMZN", "HPQ"],
            "Software - Infrastructure": ["ORCL", "AMZN", "GOOGL", "AAPL"],
            "Software - Application": ["CRM", "SAP", "INTU", "NOW"],
            "Semiconductors": ["AMD", "INTC", "TXN", "QCOM"],
            "Internet Retail": ["BABA", "JD", "EBAY", "MELI"],
            "Entertainment": ["DIS", "WBD", "PARA", "SONY"]
        }
        raw_peers = industry_map.get(industry, ["SPY"])
        peer_tickers = [p for p in raw_peers if p.lower() != (symbol or "").lower()][:3]

    if peer_tickers:
        context_parts.append("\n### Competitors & Peers Financial Summaries")
        for peer in peer_tickers:
            try:
                peer_ticker = yf.Ticker(peer)
                peer_info = peer_ticker.info or {}
                context_parts.append(f"\n#### Peer Ticker: {peer} ({peer_info.get('longName', peer)})")
                context_parts.append(f"Peer Industry: {peer_info.get('industry', 'n/a')}")
                peer_fin = peer_ticker.financials
                if peer_fin is not None and not peer_fin.empty:
                    rows = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
                    available_rows = [r for r in rows if r in peer_fin.index]
                    peer_fin_summary = peer_fin.loc[available_rows].iloc[:, :3]
                    context_parts.append(df_to_markdown(peer_fin_summary))
            except Exception as e:
                context_parts.append(f"Failed to fetch financials for peer {peer}: {e}")

    # 4. Search Fallback for transcripts & latest filings
    queries = [
        f"{company_name} latest earnings call transcript Q4 Q3 2025 2026 investor presentation operational KPIs",
        f"{company_name} competitors peers benchmarking industry average gross margin debt equity 2025 2026"
    ]
    for q in queries:
        url = 'https://lite.duckduckgo.com/lite/'
        data = urllib.parse.urlencode({'q': q}).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')
                links = soup.find_all('a', class_='result-link')
                snippets = soup.find_all('td', class_='result-snippet')
                
                context_parts.append(f"\n### Search Results for: {q}")
                for i in range(min(3, len(links), len(snippets))):
                    context_parts.append(
                        f"Title: {links[i].text.strip()}\n"
                        f"URL: {links[i]['href']}\n"
                        f"Snippet: {snippets[i].text.strip()}\n"
                        f"---"
                    )
            time.sleep(1)
        except Exception as e:
            context_parts.append(f"\nSearch fallback failed for query '{q}': {e}")
            
    return "\n".join(context_parts)


AGENT_INSTRUCTIONS = """You are a senior equity research analyst specializing in financial and operational performance assessment of publicly listed companies.
Analyze the provided search results context and construct a highly concise, high-density financial and operational performance report in an executive-summary style. Focus on bullets and tables to save tokens.

IMPORTANT: You must output the entire response as a single, valid JSON object ONLY. Do not wrap the JSON in markdown code blocks (such as ```json) and do not output any leading or trailing conversational text. Begin your response with '{' and end with '}'.

### JSON Schema:
{
  "identity_header": {
    "legal_name": "string",
    "ticker_exchange": "string",
    "fy_end": "string",
    "currency": "string",
    "sector_industry": "string",
    "as_of_date": "string"
  },
  "performance_summary": {
    "health_and_trajectory": "string (1 tight paragraph)",
    "improving": ["string"],
    "deteriorating": ["string"],
    "uncertain": ["string"]
  },
  "financial_performance_analysis": {
    "key_metrics_table": [
      { "metric": "string", "fy_minus_2": "string", "fy_minus_1": "string", "fy_latest": "string", "sources": "string" }
    ],
    "ratios_dashboard": {
      "growth": "string (metric name, values, trajectory arrow, brief driver)",
      "margins": "string",
      "returns": "string",
      "leverage_coverage": "string",
      "liquidity": "string"
    },
    "narrative_analysis": "string (highly concise, executive style)"
  },
  "operational_performance_analysis": {
    "sector_kpi_table": [
      { "kpi_name": "string", "fy_minus_2": "string", "fy_minus_1": "string", "fy_latest": "string" }
    ],
    "narrative": "string (highly concise, includes quotes if any)"
  },
  "benchmarking_vs_peers": {
    "comparison_table": [
      { "company": "string", "revenue": "string", "operating_margin": "string", "net_debt": "string" }
    ],
    "relative_standing": "string (leads, in-line, lags, quantifying the gap)"
  },
  "source_log_and_gaps": {
    "sources": [
      { "document": "string", "url": "string", "key_data": "string" }
    ],
    "data_gaps": [
      { "gap_description": "string", "impact": "string" }
    ]
  }
}
"""


@node
def format_prompt(node_input: str) -> str:
    """Combines the instructions and search context into a single user prompt
    to avoid setting developer instructions on models that do not support it.
    """
    return f"{AGENT_INSTRUCTIONS}\n\nSearch Context Data:\n{node_input}"


performance_assessor = LlmAgent(
    name="performance_assessor",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="",
)

root_agent = Workflow(
    name="financial_operational_performance_assessment",
    edges=[
        Edge(from_node=START, to_node=retrieve_stock_data),
        Edge(from_node=retrieve_stock_data, to_node=format_prompt),
        Edge(from_node=format_prompt, to_node=performance_assessor),
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)
