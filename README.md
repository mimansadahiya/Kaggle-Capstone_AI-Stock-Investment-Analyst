# Kaggle Capstone: AI Stock Investment Analyst

An AI-powered agentic system designed to analyze stock market data, perform fundamental and technical analysis, and generate comprehensive investment research reports and recommendations.

## Project Overview
This project builds an automated AI Investment Analyst that aggregates data from multiple sources (price history, financial statements, news/market sentiment) and uses machine learning alongside Large Language Models (LLMs) to perform deep stock analysis and portfolio optimization.

## Key Features
- **Data Ingestion**: Integrates market data from APIs like Yahoo Finance (`yfinance`), Alpha Vantage, or SEC filings.
- **Technical Analysis**: Computes technical indicators (e.g., Moving Averages, RSI, MACD, Bollinger Bands).
- **Fundamental Analysis**: Parses balance sheets, income statements, and cash flow statements to compute key financial ratios (P/E, Debt-to-Equity, ROE).
- **Sentiment Analysis**: Analyzes financial news headlines and financial reports to gauge market sentiment.
- **AI Analyst Reports**: Uses LLMs to synthesize findings, evaluate investment risks, and write institutional-grade analyst reports.
- **Backtesting & Portfolio Optimization**: Evaluates investment strategies using historic data to calculate metrics like Sharpe Ratio and Maximum Drawdown.

## Project Structure
```text
├── data/                    # Local data storage (ignored by git)
├── notebooks/               # Jupyter notebooks for EDA and prototyping
├── src/                     # Core source code
│   ├── data_ingestion.py    # APIs for fetching market and fundamental data
│   ├── indicators.py        # Technical and fundamental feature calculators
│   ├── agent.py             # LLM orchestration and analyst report generation
│   └── portfolio.py         # Backtesting and portfolio optimization engine
├── tests/                   # Unit and integration tests
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Getting Started

### Prerequisites
- Python 3.9+
- Pip package manager

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/mimansadahiya/Kaggle-Capstone_AI-Stock-Investment-Analyst.git
   cd Kaggle-Capstone_AI-Stock-Investment-Analyst
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
