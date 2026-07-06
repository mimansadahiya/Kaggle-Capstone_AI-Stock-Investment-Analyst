import json
import urllib.request
import urllib.parse
import yfinance as yf
import pandas as pd

def lookup_ticker(company_name: str) -> str:
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(company_name)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            quotes = data.get('quotes', [])
            if quotes:
                return quotes[0].get('symbol')
    except Exception as e:
        print(f"Ticker lookup failed: {e}")
    return None

def get_peers_by_industry(industry: str, target_symbol: str) -> list:
    # Basic mapping of popular industries to major tickers
    industry_map = {
        "Auto Manufacturers": ["F", "GM", "RIVN", "BYDDY"],
        "Consumer Electronics": ["MSFT", "GOOGL", "AMZN", "HPQ"],
        "Software - Infrastructure": ["ORCL", "AMZN", "GOOGL", "AAPL"],
        "Software - Application": ["CRM", "SAP", "INTU", "NOW"],
        "Semiconductors": ["AMD", "INTC", "TXN", "QCOM"],
        "Internet Retail": ["BABA", "JD", "EBAY", "MELI"],
        "Entertainment": ["DIS", "WBD", "PARA", "SONY"]
    }
    peers = industry_map.get(industry, ["SPY"])
    return [p for p in peers if p.lower() != target_symbol.lower()][:3]

def compile_context(company_name: str) -> str:
    symbol = lookup_ticker(company_name)
    if not symbol:
        return f"Could not find ticker symbol for company: {company_name}"
        
    print(f"Retrieving data for {company_name} ({symbol})...", flush=True)
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    
    context_parts = []
    context_parts.append(f"Target Entity: {company_name}")
    context_parts.append(f"Ticker Symbol: {symbol}")
    context_parts.append(f"Legal Name: {info.get('longName', company_name)}")
    context_parts.append(f"Sector: {info.get('sector', 'n/a')}")
    context_parts.append(f"Industry: {info.get('industry', 'n/a')}")
    context_parts.append(f"Exchange: {info.get('exchange', 'n/a')}")
    context_parts.append(f"Currency: {info.get('financialCurrency', 'USD')}")
    
    # Financial tables helper
    def df_to_markdown(df):
        if df is None or df.empty:
            return "n/a — not available"
        df.columns = [str(c)[:10] for c in df.columns]
        # Clean index names
        df.index = [str(i) for i in df.index]
        headers = ["Metric"] + list(df.columns)
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for idx, row in df.iterrows():
            row_vals = []
            for val in row.values:
                if pd.isna(val):
                    row_vals.append("n/a")
                elif isinstance(val, (int, float)):
                    row_vals.append(f"{val:,.2f}" if val % 1 != 0 else f"{int(val):,}")
                else:
                    row_vals.append(str(val))
            row_str = f"| {idx} | " + " | ".join(row_vals) + " |"
            lines.append(row_str)
        return "\n".join(lines)

    context_parts.append("\n### Target Company Financial Statements (Last 3-4 Years)")
    context_parts.append("#### Income Statement:")
    context_parts.append(df_to_markdown(ticker.financials))
    
    context_parts.append("#### Balance Sheet:")
    context_parts.append(df_to_markdown(ticker.balance_sheet))
    
    context_parts.append("#### Cash Flow:")
    context_parts.append(df_to_markdown(ticker.cashflow))
    
    # Get peers and benchmark
    industry = info.get('industry', '')
    peers = get_peers_by_industry(industry, symbol)
    context_parts.append(f"\n### Competitors & Peers ({', '.join(peers)})")
    
    for peer in peers:
        print(f"Retrieving peer data for {peer}...", flush=True)
        try:
            peer_ticker = yf.Ticker(peer)
            peer_info = peer_ticker.info or {}
            context_parts.append(f"\n#### Peer: {peer_info.get('longName', peer)} ({peer})")
            context_parts.append(f"Peer Industry: {peer_info.get('industry', 'n/a')}")
            # Add small income statement summary
            peer_fin = peer_ticker.financials
            if peer_fin is not None and not peer_fin.empty:
                # Limit to latest 3 columns and key rows
                rows = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
                available_rows = [r for r in rows if r in peer_fin.index]
                peer_fin_summary = peer_fin.loc[available_rows].iloc[:, :3]
                context_parts.append(df_to_markdown(peer_fin_summary))
        except Exception as e:
            context_parts.append(f"Failed to fetch peer data for {peer}: {e}")
            
    return "\n".join(context_parts)

if __name__ == "__main__":
    report = compile_context("Tesla")
    print(report[:2000])
