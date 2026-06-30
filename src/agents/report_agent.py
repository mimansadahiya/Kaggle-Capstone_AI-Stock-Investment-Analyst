import os
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class ReportAgent:
    """
    Sub-agent responsible for aggregating data from other agents and
    synthesizing an institutional-grade investment research report.
    """
    def __init__(self):
        # Check for both standard environment variable keys
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def generate_report(
        self,
        info: Dict[str, Any],
        technical_data: Dict[str, Any],
        fundamental_data: Dict[str, Any],
        valuation_data: Dict[str, Any],
        risk_data: Dict[str, Any]
    ) -> str:
        """
        Synthesizes the analyst report using Gemini LLM, with a robust fallback.
        """
        # Construct the prompt with all stock analysis metrics
        ticker = info.get('symbol', 'Unknown Ticker')
        company_name = info.get('shortName', 'the company')
        sector = info.get('sector', 'Unknown Sector')
        industry = info.get('industry', 'Unknown Industry')
        summary = info.get('longBusinessSummary', 'No description available.')
        current_price = info.get('currentPrice') or info.get('regularMarketPreviousClose') or "N/A"

        prompt = f"""
You are an expert, institutional-grade AI Stock Investment Analyst.
Generate a comprehensive, professional investment research report for {company_name} (Ticker: {ticker}).

Sector: {sector}
Industry: {industry}
Current Price: ${current_price}

--- Company Overview ---
{summary}

--- Technical Indicators ---
- 20-Day SMA: {technical_data.get('SMA_20', 'N/A')}
- 50-Day SMA: {technical_data.get('SMA_50', 'N/A')}
- 200-Day SMA: {technical_data.get('SMA_200', 'N/A')}
- RSI (14-day): {technical_data.get('RSI_14', 'N/A')}
- MACD Line: {technical_data.get('MACD', 'N/A')}
- MACD Signal Line: {technical_data.get('MACD_Signal', 'N/A')}

--- Fundamental Metrics ---
- P/E Ratio: {fundamental_data.get('pe_ratio', 'N/A')}
- P/B Ratio: {fundamental_data.get('pb_ratio', 'N/A')}
- Profit Margin: {fundamental_data.get('profit_margin', 'N/A')}
- ROE: {fundamental_data.get('roe', 'N/A')}
- Debt-to-Equity: {fundamental_data.get('debt_to_equity', 'N/A')}
- Dividend Yield: {fundamental_data.get('dividend_yield', 'N/A')}

--- Intrinsic Valuation ---
- DCF Intrinsic Value: {valuation_data.get('intrinsic_value', 'N/A')} (WACC used: {valuation_data.get('calculated_wacc', 'N/A')})
- DCF Projections: {valuation_data.get('fcf_projections', 'N/A')}
- Multiples Target Price: {valuation_data.get('target_price', 'N/A')} (Sector Multiple used: {valuation_data.get('multiple_used', 'N/A')})

--- Risk Analysis ---
- Annualized Volatility: {risk_data.get('annualized_volatility', 'N/A')}
- Value at Risk (95% Daily): {risk_data.get('var_95', 'N/A')}
- Beta (vs Market): {risk_data.get('beta', 'N/A')}
- Maximum Drawdown: {risk_data.get('max_drawdown', 'N/A')}

--- REPORT INSTRUCTIONS ---
Please synthesize all the sections above. Provide a structured research report with:
1. **Executive Summary**: A concise investment thesis.
2. **Technical Analysis Evaluation**: Trend analysis (bullish, bearish, neutral) based on SMAs, RSI, MACD.
3. **Fundamental Analysis Evaluation**: Analysis of profitability, safety (debt), and efficiency (ROE).
4. **Valuation Assessment**: Compare current price with intrinsic DCF value and multiples target.
5. **Risk Assessment**: Analyze key volatility and downside risks (VaR, beta, maximum drawdown).
6. **Recommendation & Target Price**: Clear "BUY", "SELL", or "HOLD" recommendation, with a 12-month target price and rationale.

Use professional, markdown-formatted investment banking style layout. Do not use generic text.
"""

        if not self.api_key:
            return self._generate_fallback_report(ticker, company_name, current_price, fundamental_data, valuation_data, risk_data)

        try:
            # Call Gemini 2.5 Flash API directly using requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            else:
                return f"""### API Error (Status {response.status_code})
Failed to fetch LLM response. 
Response Body: {response.text}

---

{self._generate_fallback_report(ticker, company_name, current_price, fundamental_data, valuation_data, risk_data)}"""

        except Exception as e:
            return f"""### Connection Exception
Failed to call Gemini API: {e}

---

{self._generate_fallback_report(ticker, company_name, current_price, fundamental_data, valuation_data, risk_data)}"""

    def _generate_fallback_report(
        self,
        ticker: str,
        company_name: str,
        current_price: Any,
        fundamental_data: Dict[str, Any],
        valuation_data: Dict[str, Any],
        risk_data: Dict[str, Any]
    ) -> str:
        """
        Generates a high-quality programmatic report fallback when LLM API is unavailable.
        """
        # Determine recommendation dynamically
        dcf_val = valuation_data.get('intrinsic_value')
        curr = float(current_price) if isinstance(current_price, (int, float)) else None
        
        recommendation = "HOLD"
        target_price = "N/A"
        rationale = "Insufficient valuation data to determine target."

        if dcf_val and curr:
            target_price = dcf_val
            upside = (dcf_val - curr) / curr
            if upside > 0.15:
                recommendation = "BUY"
                rationale = f"Stock is significantly undervalued, trading at a {round(upside*100, 1)}% discount to its DCF intrinsic value of ${dcf_val}."
            elif upside < -0.15:
                recommendation = "SELL"
                rationale = f"Stock is overvalued compared to its DCF intrinsic value of ${dcf_val}. Estimated downside of {round(abs(upside)*100, 1)}%."
            else:
                recommendation = "HOLD"
                rationale = f"Stock is fairly valued. Current price is within 15% of the DCF intrinsic value of ${dcf_val}."

        pe = fundamental_data.get('pe_ratio')
        beta = risk_data.get('beta')
        debt_eq = fundamental_data.get('debt_to_equity')

        pe_assessment = f"P/E ratio of {pe} represents a standard multiple." if pe else "P/E data unavailable."
        beta_assessment = f"Beta of {beta} indicates the stock is {'more volatile than the market' if beta and beta > 1 else 'less volatile than the market'}." if beta else "Beta data unavailable."
        debt_assessment = f"Debt-to-equity is {debt_eq}, reflecting {'healthy leverage' if debt_eq and debt_eq < 1.5 else 'elevated debt leverage'}." if debt_eq else "Leverage metrics unavailable."

        return f"""> [!NOTE]
> **API Key Missing**: A Gemini API key was not found. To enable full AI-generated research reports, set a `GEMINI_API_KEY` in a `.env` file in the project root directory. Below is a rule-based backup report.

# Investment Research Report (Automated Summary)
**Ticker**: {ticker} | **Company**: {company_name} | **Current Price**: ${current_price}

---

## 1. Valuation & Recommendation
- **Current Analyst Rating**: **{recommendation}**
- **12-Month Target Price**: **${target_price}**
- **Rationale**: {rationale}

---

## 2. Fundamental Assessment
- **Valuation Multiples**: {pe_assessment}
- **Financial Leverage**: {debt_assessment}
- **Returns Profile**: Return on Equity (ROE) is currently {fundamental_data.get('roe', 'N/A')} and Profit Margin is {fundamental_data.get('profit_margin', 'N/A')}.

---

## 3. Risk Assessment
- **Systematic Risk**: {beta_assessment}
- **Historical Downside**: The maximum drawdown observed in the historical period is {risk_data.get('max_drawdown', 'N/A')}.
- **Value at Risk (95%)**: Value at Risk (95% daily confidence) is {risk_data.get('var_95', 'N/A')}, meaning there is a 5% chance of a daily loss exceeding this percentile return.
"""
