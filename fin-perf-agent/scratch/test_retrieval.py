import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def retrieve_stock_data(company_name: str) -> str:
    queries = [
        f"{company_name} primary listing legal name ticker exchange ISIN FY-end reporting currency",
        f"{company_name} latest 10-K annual report FY 2025 FY 2024 2026 financial statements revenue net income",
        f"{company_name} latest earnings call transcript Q4 Q3 2025 2026 investor presentation operational KPIs",
        f"{company_name} competitors peers latest financial benchmarking 2025 2026 gross margin debt equity"
    ]
    
    context_parts = []
    context_parts.append(f"Target Entity: {company_name}\n")
    
    for q in queries:
        print(f"Executing search query: {q}", flush=True)
        url = 'https://lite.duckduckgo.com/lite/'
        data = urllib.parse.urlencode({'q': q}).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')
                links = soup.find_all('a', class_='result-link')
                snippets = soup.find_all('td', class_='result-snippet')
                
                print(f"  Found {len(links)} links", flush=True)
                context_parts.append(f"### Search Results for: {q}")
                for i in range(min(5, len(links), len(snippets))):
                    context_parts.append(
                        f"Title: {links[i].text.strip()}\n"
                        f"URL: {links[i]['href']}\n"
                        f"Snippet: {snippets[i].text.strip()}\n"
                        f"---"
                    )
                context_parts.append("\n")
            time.sleep(1)
        except Exception as e:
            print(f"  Query failed: {e}", flush=True)
            context_parts.append(f"Failed query '{q}': {e}\n")
            
    return "\n".join(context_parts)

if __name__ == "__main__":
    res = retrieve_stock_data("Tesla")
    print(f"Total context length: {len(res)}")
    print("Snippet:")
    print(res[:2000])
