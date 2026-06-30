import pandas as pd
import yfinance as yf
from typing import Dict, Any, Optional

class DataFetcher:
    """
    Handles data ingestion from Yahoo Finance (yfinance) for stock analysis.
    """
    def __init__(self, ticker: str):
        self.ticker_str = ticker.upper()
        self.ticker = yf.Ticker(self.ticker_str)

    def get_info(self) -> Dict[str, Any]:
        """
        Retrieves general company metadata and reference points.
        """
        try:
            info = self.ticker.info
            if not info or 'symbol' not in info:
                # Return basic fallback if info is empty or fails
                return {
                    "symbol": self.ticker_str,
                    "shortName": self.ticker_str,
                    "sector": "Unknown",
                    "industry": "Unknown",
                    "longBusinessSummary": "No summary available."
                }
            return info
        except Exception as e:
            print(f"Error fetching info for {self.ticker_str}: {e}")
            return {
                "symbol": self.ticker_str,
                "shortName": self.ticker_str,
                "sector": "Unknown",
                "industry": "Unknown",
                "longBusinessSummary": "No summary available."
            }

    def get_historical_prices(self, period: str = "1y") -> pd.DataFrame:
        """
        Fetches historical price data.
        """
        try:
            df = self.ticker.history(period=period)
            if df.empty:
                raise ValueError(f"No historical data returned for {self.ticker_str}")
            return df
        except Exception as e:
            print(f"Error fetching history for {self.ticker_str}: {e}")
            return pd.DataFrame()

    def get_financial_statements(self) -> Dict[str, pd.DataFrame]:
        """
        Retrieves balance sheets, income statements, and cash flows.
        """
        try:
            return {
                "balance_sheet": self.ticker.balance_sheet,
                "income_stmt": self.ticker.financials,
                "cashflow": self.ticker.cashflow
            }
        except Exception as e:
            print(f"Error fetching financial statements for {self.ticker_str}: {e}")
            return {
                "balance_sheet": pd.DataFrame(),
                "income_stmt": pd.DataFrame(),
                "cashflow": pd.DataFrame()
            }
