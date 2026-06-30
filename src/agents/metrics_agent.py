import pandas as pd
import numpy as np
from typing import Dict, Any

class MetricsAgent:
    """
    Sub-agent responsible for calculating fundamental and technical metrics.
    """
    def __init__(self):
        pass

    def compute_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes SMA, EMA, RSI, and MACD for historical stock prices.
        """
        if df.empty or 'Close' not in df.columns:
            return df

        df = df.copy()

        # Simple Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()

        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

        # Relative Strength Index (RSI) - 14 day
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).copy()
        loss = (-delta.where(delta < 0, 0)).copy()

        # Use Wilder's moving average smoothing approach for RSI
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        # Avoid division by zero
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df['RSI_14'] = 100 - (100 / (1 + rs))
        df['RSI_14'] = df['RSI_14'].fillna(50)  # Default neutral RSI if not enough data

        return df

    def compute_fundamental_metrics(self, info: Dict[str, Any], financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Extracts and calculates fundamental financial ratios.
        """
        metrics = {}

        # 1. Try to extract directly from yfinance info
        metrics['pe_ratio'] = info.get('trailingPE') or info.get('forwardPE')
        metrics['pb_ratio'] = info.get('priceToBook')
        metrics['profit_margin'] = info.get('profitMargins')
        metrics['roe'] = info.get('returnOnEquity')
        metrics['debt_to_equity'] = info.get('debtToEquity')
        metrics['dividend_yield'] = info.get('dividendYield')

        # Convert percentage debt_to_equity (e.g. 120.5) to decimal ratio (e.g. 1.205) if needed
        if metrics['debt_to_equity'] is not None and metrics['debt_to_equity'] > 2:
            metrics['debt_to_equity'] = metrics['debt_to_equity'] / 100.0

        # 2. Back up calculations from financial statements if info fields are missing
        balance_sheet = financials.get('balance_sheet', pd.DataFrame())
        income_stmt = financials.get('income_stmt', pd.DataFrame())

        if not balance_sheet.empty and not income_stmt.empty:
            try:
                # Helper to find row values in dataframes with varying index labels
                def get_row_value(df: pd.DataFrame, keys: list) -> Optional[float]:
                    for key in keys:
                        # Match index ignoring case and whitespace
                        matched_index = [idx for idx in df.index if str(idx).strip().lower() == key.strip().lower()]
                        if matched_index:
                            # Return latest period value (first column)
                            val = df.loc[matched_index[0]].iloc[0]
                            if pd.notna(val):
                                return float(val)
                    return None

                # Compute Debt to Equity
                if metrics['debt_to_equity'] is None:
                    tot_liab = get_row_value(balance_sheet, ['Total Liabilities Net Minor Interest', 'Total Liabilities'])
                    tot_equity = get_row_value(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity'])
                    if tot_liab and tot_equity:
                        metrics['debt_to_equity'] = tot_liab / tot_equity

                # Compute Return on Equity (ROE)
                if metrics['roe'] is None:
                    net_inc = get_row_value(income_stmt, ['Net Income'])
                    tot_equity = get_row_value(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity'])
                    if net_inc and tot_equity:
                        metrics['roe'] = net_inc / tot_equity

                # Compute Profit Margin
                if metrics['profit_margin'] is None:
                    net_inc = get_row_value(income_stmt, ['Net Income'])
                    tot_rev = get_row_value(income_stmt, ['Total Revenue'])
                    if net_inc and tot_rev:
                        metrics['profit_margin'] = net_inc / tot_rev

            except Exception as e:
                print(f"Error calculating fundamental fallback metrics: {e}")

        # Ensure all None values have defaults or clean representations
        return {k: (round(v, 4) if isinstance(v, (int, float)) else v) for k, v in metrics.items()}
