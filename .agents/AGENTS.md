# Workspace Rules: AI Stock Investment Analyst

This workspace contains code and configurations for building an AI-powered stock investment analyst.

## System Goals
1. **Modular Agent Architecture**: Implement separate, dedicated components (valuation, risk analysis, fundamental/technical metrics) to analyze stocks.
2. **Quality & Testability**: Write clean, modular Python code. Every calculator and ingestion script should have corresponding unit tests.
3. **Data Security**: Keep private keys, API credentials, and fetched data files out of version control.
4. **User-Friendly Delivery**: Build a web application (e.g., Streamlit or a lightweight web dashboard) to render analyst reports, charts, and recommendations.

## Coding Guidelines
- **Python**: Use Python 3.9+ features, type hinting where applicable, and write clear docstrings for all functions.
- **Libraries**: Prioritize standard libraries and lightweight packages (`yfinance`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`).
- **File Structure**: Keep all core modules inside the `src/` directory.

## Directory Structure Roles
- `/src`: Primary source code (data ingestion, analysis, agent logic, UI).
- `/notebooks`: Exploratory analysis and prototyping.
- `/tests`: Test suites.

## Agent Implementations & Security Policies
- **Agent 3 (Competitive Landscape)**: Uses Google Search Grounding to identify competitors, analyze market share, and track competitor updates.
- **Agent 4 (News & Sentiments)**: Uses Google Search Grounding to aggregate news from top channels and evaluate customer/social media sentiment.
- **Agent 8 (Major Risks)**: Uses Google Search Grounding to evaluate strategic, operational, financial, and GRC risks.
- **API Key Security**: The Streamlit sidebar will include an optional input field for users to provide their own `GEMINI_API_KEY`, falling back to local environment variables or rule-based reports.

