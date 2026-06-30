import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class ValuationAgent:
    """
    Sub-agent responsible for intrinsic stock valuation (DCF and Multiples).
    """
    def __init__(self):
        pass

    def run_dcf_valuation(
        self,
        info: Dict[str, Any],
        financials: Dict[str, pd.DataFrame],
        risk_free_rate: float = 0.045,  # 4.5% default US 10-Yr Yield
        market_return: float = 0.10,    # 10% historical stock market return
        growth_rate: float = 0.05,       # 5% default short-term growth rate
        terminal_growth: float = 0.025   # 2.5% long-term inflation/GDP rate
    ) -> Dict[str, Any]:
        """
        Performs a basic 5-year Discounted Cash Flow (DCF) valuation.
        """
        result = {
            "intrinsic_value": None,
            "calculated_wacc": None,
            "fcf_projections": [],
            "status": "Incomplete Data"
        }

        # Retrieve financial statements
        balance_sheet = financials.get("balance_sheet", pd.DataFrame())
        income_stmt = financials.get("income_stmt", pd.DataFrame())
        cashflow = financials.get("cashflow", pd.DataFrame())

        if balance_sheet.empty or income_stmt.empty or cashflow.empty:
            return result

        # Helper to find values across index labels
        def get_row(df: pd.DataFrame, keys: list) -> Optional[pd.Series]:
            for key in keys:
                matched_index = [idx for idx in df.index if str(idx).strip().lower() == key.strip().lower()]
                if matched_index:
                    return df.loc[matched_index[0]]
            return None

        try:
            # 1. Calculate Free Cash Flow (FCF) = Operating Cash Flow - Capital Expenditures
            op_cash_flow = get_row(cashflow, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
            cap_ex = get_row(cashflow, ['Capital Expenditure', 'Capital Expenditures'])

            if op_cash_flow is None:
                return result

            # Capital expenditure is often negative in cash flow statements, adjust accordingly
            if cap_ex is not None:
                fcf_series = op_cash_flow + cap_ex  # e.g., $100M + (-$30M) = $70M FCF
            else:
                # Fallback if capital expenditures is missing, assume Capex is 20% of Operating Cash Flow
                fcf_series = op_cash_flow * 0.8

            latest_fcf = float(fcf_series.iloc[0])
            if pd.isna(latest_fcf) or latest_fcf <= 0:
                # If latest FCF is negative, try using average of past 3 years or fallback
                valid_fcfs = fcf_series.dropna()
                if len(valid_fcfs) > 1 and valid_fcfs.mean() > 0:
                    latest_fcf = float(valid_fcfs.mean())
                else:
                    return {**result, "status": "Negative or invalid latest Free Cash Flow"}

            # 2. Determine WACC (Discount Rate) using CAPM
            beta = info.get('beta')
            if beta is None or pd.isna(beta):
                beta = 1.0  # Default to market beta if missing

            # CAPM: Cost of Equity = Rf + Beta * (Rm - Rf)
            cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
            
            # For simplicity, if debt info is missing, default WACC to Cost of Equity or 9.0%
            wacc = max(cost_of_equity, 0.08) # floor at 8% WACC
            result["calculated_wacc"] = round(wacc, 4)

            # 3. Project Free Cash Flows for 5 Years
            projected_fcfs = []
            current_fcf = latest_fcf
            for year in range(1, 6):
                current_fcf = current_fcf * (1 + growth_rate)
                projected_fcfs.append(current_fcf)

            # 4. Calculate Terminal Value
            terminal_value = (projected_fcfs[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)

            # 5. Discount FCFs and Terminal Value to Present Value (PV)
            pv_fcfs = [fcf / ((1 + wacc) ** year) for year, fcf in enumerate(projected_fcfs, 1)]
            pv_terminal_value = terminal_value / ((1 + wacc) ** 5)
            enterprise_value = sum(pv_fcfs) + pv_terminal_value

            # 6. Adjust for Net Debt to get Equity Value
            cash_row = get_row(balance_sheet, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Cash'])
            total_debt_row = get_row(balance_sheet, ['Total Debt', 'Long Term Debt', 'Long Term Debt Total'])

            cash = float(cash_row.iloc[0]) if cash_row is not None and pd.notna(cash_row.iloc[0]) else 0.0
            debt = float(total_debt_row.iloc[0]) if total_debt_row is not None and pd.notna(total_debt_row.iloc[0]) else 0.0

            equity_value = enterprise_value + cash - debt

            # 7. Calculate Price Per Share
            shares_outstanding = info.get('sharesOutstanding')
            if not shares_outstanding or pd.isna(shares_outstanding):
                return {**result, "status": "Missing shares outstanding data"}

            intrinsic_value = equity_value / shares_outstanding
            
            result["intrinsic_value"] = round(intrinsic_value, 2)
            result["fcf_projections"] = [round(val, 2) for val in projected_fcfs]
            result["status"] = "Success"

        except Exception as e:
            result["status"] = f"Calculation error: {e}"

        return result

    def run_multiples_valuation(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimates stock valuation based on price multiples.
        """
        eps = info.get('trailingEps') or info.get('forwardEps')
        pe_ratio = info.get('trailingPE')
        
        # Look up forward PE and industry PE comparisons if possible
        # Default target multiples if industry multiples are missing
        sector = info.get('sector', 'Unknown').lower()
        default_pe = 20.0
        if 'technology' in sector:
            default_pe = 25.0
        elif 'financial' in sector:
            default_pe = 15.0
        elif 'utilities' in sector:
            default_pe = 17.0

        if not eps or pd.isna(eps):
            return {
                "target_price": None,
                "multiple_used": default_pe,
                "status": "Missing EPS data"
            }

        # Multiples calculation: Target Price = EPS * Sector PE
        target_price = eps * default_pe

        return {
            "target_price": round(target_price, 2),
            "multiple_used": default_pe,
            "status": "Success"
        }
