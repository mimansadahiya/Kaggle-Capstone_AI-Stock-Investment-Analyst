import pandas as pd
import numpy as np
from typing import Dict, Any

class RiskAgent:
    """
    Sub-agent responsible for stock risk assessment and calculations.
    """
    def __init__(self):
        pass

    def analyze_risk(self, df: pd.DataFrame, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes historical volatility, Value at Risk (VaR), beta, and max drawdown.
        """
        result = {
            "annualized_volatility": None,
            "var_95": None,
            "beta": info.get('beta'),
            "max_drawdown": None,
            "status": "Incomplete Data"
        }

        if df.empty or 'Close' not in df.columns:
            return result

        try:
            # 1. Calculate Daily Returns
            returns = df['Close'].pct_change().dropna()
            
            if returns.empty:
                return {**result, "status": "Insufficient historical returns data"}

            # 2. Annualized Volatility
            # Volatility = daily standard deviation * sqrt(252 trading days)
            daily_std = float(returns.std())
            annualized_vol = daily_std * np.sqrt(252)
            result["annualized_volatility"] = round(annualized_vol, 4)

            # 3. Value at Risk (VaR) at 95% Confidence Level
            # Historical method: 5th percentile of daily returns
            var_95_val = float(np.percentile(returns, 5))
            result["var_95"] = round(var_95_val, 4)

            # 4. Maximum Drawdown
            cumulative_max = df['Close'].cummax()
            drawdowns = (df['Close'] - cumulative_max) / cumulative_max
            max_dd = float(drawdowns.min())
            result["max_drawdown"] = round(max_dd, 4)

            result["status"] = "Success"

        except Exception as e:
            result["status"] = f"Calculation error: {e}"

        return result
