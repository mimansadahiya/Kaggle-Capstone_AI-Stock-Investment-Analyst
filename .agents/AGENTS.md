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
