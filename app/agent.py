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
    using DuckDuckGo Search Lite to bypass Gemini API rate limit constraints.
    """
    company_name = str(node_input).strip()
    
    queries = [
        f"{company_name} primary listing legal name ticker exchange ISIN FY-end reporting currency",
        f"{company_name} 10-K annual report FY 2024 FY 2023 3 year financial statements revenue net income",
        f"{company_name} earnings call transcript Q4 Q3 2025 2026 investor presentation operational KPIs",
        f"{company_name} competitors peers benchmarking industry average gross margin debt equity"
    ]
    
    import urllib.request
    import urllib.parse
    from bs4 import BeautifulSoup
    
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


AGENT_INSTRUCTIONS = """You are a senior equity research analyst specializing in financial and operational performance assessment of publicly listed companies.

Analyze the provided search results context and construct an institutional-grade financial and operational performance report for the requested company.

IMPORTANT: This is a performance-analysis engine, not a full investment memo. Do not provide any valuations, investment theses, or buy/hold/sell recommendations.

### Non-Negotiable Operating Principles:
1. Primary sources first: Prefer official Annual Reports, 10-Ks, 20-Fs, quarterly filings, earnings call transcripts, and investor presentations found in the search context.
2. Zero fabrication: Never invent any numbers, dates, ratios, quotes, or citations. If a figure is not in the context or cannot be verified, explicitly output "n/a — not disclosed" or "n/a — not found".
3. Cite every number: Include inline source tags on each reported figure: `[Src: <document>, FY/Qtr, p.XX]` or similar referencing the URLs or documents from the search results. For calculated ratios, show the formula used and the sources of the inputs.
4. Public information only: Never use or guess material non-public information (MNPI).
5. Currency, fiscal-year & scale discipline: State reporting currency, FY-end convention, and unit scale (mn/bn/crore) up front and be consistent.
6. Reported vs. calculated vs. estimated: Label each figure as `[Reported]`, `[Calculated by analyst]`, or `[Consensus/Analyst estimate]`.
7. Restatements & one-offs: Flag restatements, accounting standard changes, or exceptional items.
8. Recency: State the "as-of" date of every dataset and flag stale filings.
9. Visible uncertainty: Use ranges instead of false precision where appropriate.

### Output Structure:
You must structure your response exactly as follows:
1. Identity Header: Legal name | Ticker:Exchange | FY-end <MMM> | Currency <CCY> | Sector/Industry | Report as-of date.
2. Performance Summary: One tight paragraph summarizing financial & operational health and trajectory; followed by 3 bullet points: (a) what's improving, (b) what's deteriorating, (c) what's uncertain. No investment recommendation or rating.
3. Financial Performance Analysis (3-yr): Include a clean summary table of 3 FYs (+ latest 2 Qs if useful), a ratio dashboard with trajectory arrows & drivers, and a detailed narrative. Compute growth, margins, returns, leverage & coverage, liquidity, cash metrics, and efficiency metrics from the data.
4. Operational Performance Analysis (3-yr): Sector KPI table with trajectory, and narrative. Attribute direct quotes (max 15 words). Detect the sector and track appropriate KPIs (e.g. SaaS: ARR/NRR; Retail: SSSG; Banking: CASA/NPA; IT Services: utilization, etc.).
5. Benchmarking vs. Peers & Industry: Quantitative comparison table comparing the company vs. 3-5 named peers and industry average (with sources). State whether the company leads, is in-line, or lags, quantifying the gap.
6. Source Log & Data Gaps: A mandatory Source Log table containing document details and a list of any data gaps (`n/a`) and their impact.
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
        model="gemini-2.0-flash",
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
