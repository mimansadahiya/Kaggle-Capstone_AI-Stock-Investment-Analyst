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
    """Retrieves stock information, financials, trading multiples, analyst recommendations,
    and peer metrics using Yahoo Finance API and DuckDuckGo fallback.
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
    # Clean common wrapper phrases
    cleaned = re.sub(r'(?i).*?valuation analysis of\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?valuation analysis for\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?valuation of\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?evaluate\s+', '', cleaned)
    cleaned = re.sub(r'(?i).*?analyze\s+', '', cleaned)
    company_name = cleaned.strip('.').strip()

    import json
    import urllib.request
    import urllib.parse
    import yfinance as yf
    import pandas as pd
    from bs4 import BeautifulSoup

    context_parts = []
    context_parts.append(f"Target Stock Query: {company_name}")

    # 1. Resolve Ticker Symbol via Yahoo Finance
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

    # 2. Get target financials & trading info
    industry = ""
    sector = ""
    if symbol:
        context_parts.append(f"Ticker Symbol: {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            
            industry = info.get('industry', '')
            sector = info.get('sector', '')
            
            context_parts.append(f"Legal Name: {info.get('longName', company_name)}")
            context_parts.append(f"Exchange: {info.get('exchange', 'n/a')}")
            context_parts.append(f"Sector: {sector}")
            context_parts.append(f"Industry: {industry}")
            context_parts.append(f"Current Price: {info.get('currentPrice', 'n/a')}")
            context_parts.append(f"Reporting Currency: {info.get('financialCurrency', 'n/a')}")
            context_parts.append(f"Market Cap: {info.get('marketCap', 'n/a')}")
            context_parts.append(f"Enterprise Value (EV): {info.get('enterpriseValue', 'n/a')}")
            
            # Multiples
            context_parts.append("\n### Valuation Multiples & Market Data")
            context_parts.append(f"Trailing P/E: {info.get('trailingPE', 'n/a')}")
            context_parts.append(f"Forward P/E: {info.get('forwardPE', 'n/a')}")
            context_parts.append(f"EV / EBITDA: {info.get('enterpriseToEbitda', 'n/a')}")
            context_parts.append(f"EV / Revenue: {info.get('enterpriseToRevenue', 'n/a')}")
            context_parts.append(f"Price to Book (P/B): {info.get('priceToBook', 'n/a')}")
            context_parts.append(f"PEG Ratio: {info.get('pegRatio', 'n/a')}")
            context_parts.append(f"Dividend Yield: {info.get('dividendYield', 'n/a')}")
            context_parts.append(f"Beta (5Y Monthly): {info.get('beta', 'n/a')}")
            context_parts.append(f"Free Cash Flow (FCF): {info.get('freeCashflow', 'n/a')}")
            context_parts.append(f"Total Debt: {info.get('totalDebt', 'n/a')}")
            context_parts.append(f"Total Cash: {info.get('totalCash', 'n/a')}")

            # Financial Tables (Filtered to prevent prompt bloat and 429 errors)
            context_parts.append("\n### Financial Statements (Latest Annual & Quarter)")
            
            # 1. Income Statement
            inc_rows = ["Total Revenue", "EBITDA", "Operating Income", "Net Income", "Diluted EPS", "EBIT"]
            fin = ticker.financials
            if fin is not None and not fin.empty:
                available_inc = [r for r in inc_rows if r in fin.index]
                context_parts.append("#### Income Statement (Annual):")
                context_parts.append(df_to_markdown(fin.loc[available_inc]))
            
            # 2. Balance Sheet
            bs_rows = ["Total Debt", "Total Cash And Short Term Investments", "Cash And Cash Equivalents", "Common Stock Equity"]
            bs = ticker.balance_sheet
            if bs is not None and not bs.empty:
                available_bs = [r for r in bs_rows if r in bs.index]
                context_parts.append("#### Balance Sheet (Annual):")
                context_parts.append(df_to_markdown(bs.loc[available_bs]))
                
            # 3. Cash Flow
            cf_rows = ["Free Cash Flow", "Capital Expenditure", "Depreciation And Amortization"]
            cf = ticker.cashflow
            if cf is not None and not cf.empty:
                available_cf = [r for r in cf_rows if r in cf.index]
                context_parts.append("#### Cash Flow (Annual):")
                context_parts.append(df_to_markdown(cf.loc[available_cf]))
            
            if ticker.quarterly_financials is not None and not ticker.quarterly_financials.empty:
                q_fin = ticker.quarterly_financials
                available_q_inc = [r for r in inc_rows if r in q_fin.index]
                context_parts.append("#### Income Statement (Quarterly):")
                context_parts.append(df_to_markdown(q_fin.loc[available_q_inc].iloc[:, :2]))

        except Exception as e:
            context_parts.append(f"Error fetching company financial statements: {e}")
    else:
        context_parts.append(f"Ticker could not be resolved for: {company_name}")

    # 3. Industry Peer Selection Map
    peer_tickers = []
    if industry:
        industry_map = {
            "Auto Manufacturers": ["F", "GM", "TSLA", "RIVN", "BYDDY"],
            "Consumer Electronics": ["AAPL", "MSFT", "GOOGL", "AMZN", "HPQ"],
            "Software - Infrastructure": ["MSFT", "ORCL", "AMZN", "GOOGL", "AAPL"],
            "Software - Application": ["CRM", "SAP", "INTU", "NOW", "WDAY"],
            "Semiconductors": ["NVDA", "AMD", "INTC", "TXN", "QCOM", "AVGO"],
            "Internet Retail": ["AMZN", "BABA", "JD", "EBAY", "MELI"],
            "Entertainment": ["NFLX", "DIS", "WBD", "PARA", "SONY"],
            "Banks - Diversified": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
            "Discount Stores": ["WMT", "TGT", "COST", "DG"],
            "Aerospace & Defense": ["BA", "LMT", "RTX", "NOC"],
        }
        raw_peers = industry_map.get(industry, [])
        if not raw_peers and sector:
            # Fallback based on sector
            sector_map = {
                "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA"],
                "Financial Services": ["JPM", "BAC", "GS", "MS"],
                "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE"],
                "Healthcare": ["JNJ", "LLY", "UNH", "PFE"],
                "Industrials": ["GE", "CAT", "HON", "UPS"],
            }
            raw_peers = sector_map.get(sector, [])
        
        peer_tickers = [p for p in raw_peers if p.lower() != (symbol or "").lower()][:4]

    if peer_tickers:
        context_parts.append("\n### Competitors & Peers Financial Summaries")
        for peer in peer_tickers:
            try:
                peer_ticker = yf.Ticker(peer)
                peer_info = peer_ticker.info or {}
                context_parts.append(f"\n#### Peer Ticker: {peer} ({peer_info.get('longName', peer)})")
                context_parts.append(f"Peer Trailing P/E: {peer_info.get('trailingPE', 'n/a')}")
                context_parts.append(f"Peer Forward P/E: {peer_info.get('forwardPE', 'n/a')}")
                context_parts.append(f"Peer EV/EBITDA: {peer_info.get('enterpriseToEbitda', 'n/a')}")
                context_parts.append(f"Peer Price/Book: {peer_info.get('priceToBook', 'n/a')}")
                context_parts.append(f"Peer PEG Ratio: {peer_info.get('pegRatio', 'n/a')}")
                context_parts.append(f"Peer EBITDA Margin: {peer_info.get('ebitdaMargins', 'n/a')}")
                context_parts.append(f"Peer Return on Equity (ROE): {peer_info.get('returnOnEquity', 'n/a')}")
            except Exception as e:
                context_parts.append(f"Failed to fetch peer metrics for {peer}: {e}")

    # 4. DuckDuckGo Fallback Search for analyst views, target prices & consensus
    queries = [
        f"{company_name} stock analyst price target consensus rating Morgan Stanley Goldman Sachs JPMorgan Jefferies 2026",
        f"{company_name} valuation analysis DCF cost of equity WACC peer multiples comparison"
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
                links = soup.find_all('a', class_={'result-link', 'result-title'})
                snippets = soup.find_all('td', class_='result-snippet')
                
                context_parts.append(f"\n### Web Search Context for: {q}")
                for i in range(min(4, len(links), len(snippets))):
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


AGENT_INSTRUCTIONS = """You are a top-tier, Goldman Sachs–calibre buy-side equity valuation analyst.
Given the financial context, construct a highly concise, source-grounded valuation analysis in an executive-summary style. 

IMPORTANT: You must output the entire response as a single, valid JSON object ONLY. Do not wrap the JSON in markdown code blocks (such as ```json) and do not output any leading or trailing conversational text. Begin your response with '{' and end with '}'.

### JSON Schema:
{
  "company_metadata": {
    "legal_name": "string",
    "ticker": "string",
    "exchange": "string",
    "sector": "string",
    "reporting_currency": "string",
    "latest_reporting_period": "string",
    "current_price": "float or null",
    "market_cap": "float or null",
    "enterprise_value": "float or null"
  },
  "verdict": {
    "fair_value_range": "string (e.g. 1850.00 - 2100.00)",
    "category": "string (undervalued / fairly valued / overvalued)",
    "upside_downside_percent": "float or null"
  },
  "supporting_pillars": {
    "dcf_pillar": "string",
    "relative_pillar": "string",
    "analyst_consensus_pillar": "string"
  },
  "dcf_valuation": {
    "assumptions": {
      "wacc_percent": "float or null",
      "terminal_growth_percent": "float or null",
      "beta": "float or null",
      "risk_free_rate_percent": "float or null",
      "erp_percent": "float or null"
    },
    "scenarios": {
      "bear": { "fcf_cagr_percent": "float or null", "implied_price": "float or null" },
      "base": { "fcf_cagr_percent": "float or null", "implied_price": "float or null" },
      "bull": { "fcf_cagr_percent": "float or null", "implied_price": "float or null" }
    },
    "sensitivity_grid": "list of dicts or nested dicts showing WACC x Terminal-Growth grid"
  },
  "relative_valuation": {
    "justification": "string explaining metric choice",
    "peer_multiples": [
      {
        "peer_ticker": "string",
        "pe_forward": "float or null",
        "ev_ebitda": "float or null",
        "price_to_book": "float or null",
        "roe_percent": "float or null"
      }
    ],
    "derived_value_range": "string"
  },
  "peer_positioning": "string (1-2 sentences tying fundamentals gap to multiple gap)",
  "analyst_commentary": {
    "consensus_rating": "string",
    "target_range": "string",
    "broker_calls": [
      { "firm": "string", "rating": "string", "target_price": "float or null", "thesis": "string" }
    ]
  },
  "assumptions_and_unknowns": ["string"],
  "sources": [{"source": "string", "metric_backed": "string", "date_pulled": "string"}],
  "standing_disclaimer": "This is a valuation analysis for informational purposes, not investment advice. Figures reflect officially available data as of the dates cited and may be stale. Verify against primary filings before any decision."
}
"""


@node
def format_prompt(node_input: str) -> str:
    """Formats instructions and context into a user prompt."""
    return f"{AGENT_INSTRUCTIONS}\n\nSearch and Financial Context Data:\n{node_input}"


valuation_analyst = LlmAgent(
    name="valuation_analyst",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="",
)

root_agent = Workflow(
    name="valuation_analysis_workflow",
    edges=[
        Edge(from_node=START, to_node=retrieve_stock_data),
        Edge(from_node=retrieve_stock_data, to_node=format_prompt),
        Edge(from_node=format_prompt, to_node=valuation_analyst),
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)
