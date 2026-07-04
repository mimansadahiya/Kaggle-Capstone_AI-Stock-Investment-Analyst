import pytest
import pandas as pd
import numpy as np
from src.agents.metrics_agent import MetricsAgent
from src.agents.valuation_agent import ValuationAgent
from src.agents.risk_agent import RiskAgent

# --- 1. Mock Data Setup ---

@pytest.fixture
def mock_historical_data():
    """
    Creates a mock pandas DataFrame with historical stock prices.
    We'll construct a 250-day simple price series.
    """
    dates = pd.date_range(start="2025-01-01", periods=250)
    # Simple sine wave trend on top of base price to guarantee variations
    prices = 100.0 + 10.0 * np.sin(np.linspace(0, 10, 250))
    df = pd.DataFrame({
        "Open": prices,
        "High": prices + 1.0,
        "Low": prices - 1.0,
        "Close": prices,
        "Volume": 1000000
    }, index=dates)
    return df

@pytest.fixture
def mock_info():
    """
    Mock yfinance info dictionary.
    """
    return {
        "symbol": "MOCK",
        "shortName": "Mock Company",
        "sector": "Technology",
        "industry": "Software",
        "beta": 1.2,
        "sharesOutstanding": 10000000, # 10 Million shares
        "trailingPE": 25.0,
        "trailingEps": 4.0,
        "regularMarketPreviousClose": 100.0,
        "currentPrice": 100.0
    }

@pytest.fixture
def mock_financials():
    """
    Mock financial statement DataFrames.
    """
    # Columns represent dates
    dates = ["2025-12-31", "2024-12-31", "2023-12-31"]
    
    balance_sheet = pd.DataFrame(
        [
            [50000000.0, 40000000.0, 30000000.0],  # Cash And Cash Equivalents
            [200000000.0, 180000000.0, 150000000.0],  # Total Liabilities Net Minor Interest
            [300000000.0, 280000000.0, 250000000.0],  # Stockholders Equity
            [100000000.0, 90000000.0, 80000000.0]   # Total Debt
        ],
        index=[
            "Cash And Cash Equivalents",
            "Total Liabilities Net Minor Interest",
            "Stockholders Equity",
            "Total Debt"
        ],
        columns=dates
    )

    income_stmt = pd.DataFrame(
        [
            [40000000.0, 35000000.0, 30000000.0],  # Net Income
            [200000000.0, 180000000.0, 160000000.0]  # Total Revenue
        ],
        index=[
            "Net Income",
            "Total Revenue"
        ],
        columns=dates
    )

    cashflow = pd.DataFrame(
        [
            [60000000.0, 50000000.0, 45000000.0],  # Operating Cash Flow
            [-15000000.0, -12000000.0, -10000000.0] # Capital Expenditure
        ],
        index=[
            "Operating Cash Flow",
            "Capital Expenditure"
        ],
        columns=dates
    )

    return {
        "balance_sheet": balance_sheet,
        "income_stmt": income_stmt,
        "cashflow": cashflow
    }


# --- 2. Unit Tests ---

def test_metrics_agent_technical(mock_historical_data):
    agent = MetricsAgent()
    df_result = agent.compute_technical_indicators(mock_historical_data)
    
    # Assert columns were correctly added
    assert "SMA_20" in df_result.columns
    assert "SMA_50" in df_result.columns
    assert "SMA_200" in df_result.columns
    assert "RSI_14" in df_result.columns
    assert "MACD" in df_result.columns
    assert "MACD_Signal" in df_result.columns

    # Assert last row values are valid numbers
    latest = df_result.iloc[-1]
    assert pd.notna(latest["SMA_20"])
    assert pd.notna(latest["RSI_14"])
    assert 0 <= latest["RSI_14"] <= 100


def test_metrics_agent_fundamental(mock_info, mock_financials):
    agent = MetricsAgent()
    metrics = agent.compute_fundamental_metrics(mock_info, mock_financials)
    
    assert metrics["pe_ratio"] == 25.0
    assert metrics["pb_ratio"] is None  # Not present in info dict
    assert metrics["roe"] == round(40000000.0 / 300000000.0, 4)  # Net Income / Stockholder Equity
    assert metrics["debt_to_equity"] == round(200000000.0 / 300000000.0, 4) # Liabilities / Equity


def test_valuation_agent_dcf(mock_info, mock_financials):
    agent = ValuationAgent()
    # Execute DCF calculation
    dcf_res = agent.run_dcf_valuation(mock_info, mock_financials)
    
    assert dcf_res["status"] == "Success"
    assert dcf_res["intrinsic_value"] > 0
    assert dcf_res["calculated_wacc"] > 0
    assert len(dcf_res["fcf_projections"]) == 5


def test_valuation_agent_multiples(mock_info):
    agent = ValuationAgent()
    res = agent.run_multiples_valuation(mock_info)
    
    assert res["status"] == "Success"
    # Tech Sector target multiple = 25x. EPS = 4.0. Target = 25 * 4 = 100
    assert res["target_price"] == 100.0
    assert res["multiple_used"] == 25.0


def test_risk_agent(mock_historical_data, mock_info):
    agent = RiskAgent()
    res = agent.run_dcf_valuation = agent.analyze_risk(mock_historical_data, mock_info)
    
    assert res["status"] == "Success"
    assert res["annualized_volatility"] > 0
    assert res["var_95"] < 0  # VaR return should be negative for downside risk
    assert res["max_drawdown"] < 0  # Drawdown should be negative or zero


# --- 3. New Agent Mock Tests ---
from unittest.mock import patch, MagicMock
from src.agents.competitive_landscape_agent import CompetitiveLandscapeAgent
from src.agents.news_sentiment_agent import NewsSentimentAgent
from src.agents.major_risks_agent import MajorRisksAgent

def test_competitive_landscape_agent_missing_key():
    agent = CompetitiveLandscapeAgent()
    agent.default_api_key = None
    res = agent.analyze_competitive_landscape(None, "Apple", "AAPL", "Tech", "Consumer Elec")
    assert "Gemini API Key Missing" in res

@patch("requests.post")
def test_competitive_landscape_agent_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{"text": "===SECTION===\nKey Competitors\n===SUMMARY===\nMocked summary.\n===DETAILS===\nMocked competitive landscape analysis."}]
            }
        }]
    }
    mock_post.return_value = mock_resp

    agent = CompetitiveLandscapeAgent()
    res = agent.analyze_competitive_landscape("fake-key", "Apple", "AAPL", "Tech", "Consumer Elec")
    assert "Mocked competitive landscape analysis." in res

    # Verify Google Search Grounding configuration in payload
    called_json = mock_post.call_args[1]["json"]
    assert "tools" in called_json
    assert "google_search" in called_json["tools"][0]

@patch("requests.post")
def test_news_sentiment_agent_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{"text": "===SECTION===\nMajor News Updates\n===SUMMARY===\nMocked summary.\n===DETAILS===\nMocked news and sentiment analysis."}]
            }
        }]
    }
    mock_post.return_value = mock_resp

    agent = NewsSentimentAgent()
    res = agent.analyze_news_and_sentiment("fake-key", "Apple", "AAPL", "Consumer Elec")
    assert "Mocked news and sentiment analysis." in res

    called_json = mock_post.call_args[1]["json"]
    assert "tools" in called_json
    assert "google_search" in called_json["tools"][0]

@patch("requests.post")
def test_major_risks_agent_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{"text": "===SECTION===\nStrategic Risks\n===SUMMARY===\nMocked summary.\n===DETAILS===\nMocked major risks analysis."}]
            }
        }]
    }
    mock_post.return_value = mock_resp

    agent = MajorRisksAgent()
    res = agent.analyze_major_risks("fake-key", "Apple", "AAPL")
    assert "Mocked major risks analysis." in res

    called_json = mock_post.call_args[1]["json"]
    assert "tools" in called_json
    assert "google_search" in called_json["tools"][0]

