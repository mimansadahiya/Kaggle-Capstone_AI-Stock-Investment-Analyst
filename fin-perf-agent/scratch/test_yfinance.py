import yfinance as yf

def test_yfinance(ticker_symbol: str):
    print(f"Fetching data for {ticker_symbol}...", flush=True)
    ticker = yf.Ticker(ticker_symbol)
    
    # Info
    info = ticker.info
    print(f"Name: {info.get('longName')}")
    print(f"Sector: {info.get('sector')}")
    print(f"Industry: {info.get('industry')}")
    
    # Financials (Income Statement)
    financials = ticker.financials
    print("\nIncome Statement Columns (years):")
    print(financials.columns)
    
    # Balance Sheet
    balance_sheet = ticker.balance_sheet
    print("\nBalance Sheet Columns (years):")
    print(balance_sheet.columns)
    
    # Cash Flow
    cashflow = ticker.cashflow
    print("\nCash Flow Columns (years):")
    print(cashflow.columns)

if __name__ == "__main__":
    test_yfinance("TSLA")
