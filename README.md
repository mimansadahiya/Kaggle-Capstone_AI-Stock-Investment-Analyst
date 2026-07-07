# AI Stock Investment Analyst Dashboard

An AI-powered agentic system that generates comprehensive, institutional-grade equity research reports and interactive dashboards in minutes. By orchestrating a team of specialized qualitative sub-agents with quantitative financial models, the system helps retail investors and busy professionals get a deep, grounded view of any public stock.

🚀 **[Live Demo](https://sbk2ye3rhnke4sh2cqwylf.streamlit.app/)** | 🎬 **[Walkthrough Video](https://youtu.be/YK_Y4M_PsSo?feature=shared)**

---

## 🔑 Key Features

- **Automated Data Ingestion**: Automatically pulls historical price series, corporate profiles, and verified financial statements using Yahoo Finance (`yfinance`).
- **Interactive Valuation Suite**: Real-time adjustable financial models, including:
  - **Discounted Cash Flow (DCF)** valuation with margin-of-safety.
  - **CAPM Expected Returns** based on historical beta and risk-free inputs.
  - **Benjamin Graham Formula** intrinsic value.
  - **Institutional Price Targets** and consensus recommendations.
- **Team of Specialist Agents**: Orchestrates 7 distinct qualitative agents (Macro Outlook, Competition, News & Sentiment, Industry Dynamics, Performance, and GRC Risks) powered by `gemini-2.5-flash` and live **Google Search Grounding**.
- **Free Quota Optimization**: Built-in 6-second execution pacing and a local disk cache system (`src/cache/`) to eliminate rate-limit errors on the Gemini Free Tier.
- **Premium SaaS UI**: Clean, interactive multi-tab layout featuring a modern electric-blue theme.

---

## 📂 Project Structure

```text
├── src/
│   ├── app.py                      # Main Streamlit dashboard & orchestrator
│   ├── data_fetcher.py             # Data fetching client (yfinance integration)
│   ├── cache/                      # Local JSON cache files for ticker results
│   └── agents/                     # Modular sub-agent implementations
│       ├── company_overview_agent.py      # Profile & strategy compiler
│       ├── macro_outlook_agent.py          # Interest rates & GDP trends
│       ├── competitive_landscape_agent.py  # Peer moats & market share
│       ├── news_sentiment_agent.py         # Financial news & user sentiments
│       ├── industry_analysis_agent.py      # Market sizing & industry trends
│       ├── performance_assessor_agent.py   # Historical operational analysis
│       ├── major_risks_agent.py            # GRC & financial risk maps
│       ├── metrics_agent.py                # Mathematical ratio calculator
│       ├── valuation_agent.py              # DCF & Graham math engines
│       ├── risk_agent.py                   # Value at Risk (VaR) calculator
│       └── report_agent.py                 # Synthesis report generator
├── tests/                          # Unit & integration tests for all calculators
└── requirements.txt                # Project dependencies
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- A Gemini API Key (Optional; if not provided, the dashboard falls back to a rule-based financial analysis report).

### Installation & Run

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mimansadahiya/Kaggle-Capstone_AI-Stock-Investment-Analyst.git
   cd Kaggle-Capstone_AI-Stock-Investment-Analyst
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the web application**:
   ```bash
   streamlit run src/app.py
   ```

---

## 🧪 Testing

The math engines and API connections include comprehensive unit tests. Run them using:
```bash
pytest tests/
```
