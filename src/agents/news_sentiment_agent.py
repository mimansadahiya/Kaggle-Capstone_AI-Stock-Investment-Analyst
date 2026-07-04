import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class NewsSentimentAgent:
    """
    Sub-agent responsible for aggregating major news updates, customer reviews,
    and financial social media sentiments using Google Search Grounded Gemini API calls.
    """
    def __init__(self):
        self.default_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def analyze_news_and_sentiment(
        self,
        api_key: Optional[str],
        company_name: str,
        ticker: str,
        industry: str
    ) -> str:
        """
        Retrieves grounded news, customer, and social sentiment analysis via Gemini API with Google Search.
        """
        active_key = api_key or self.default_api_key

        if not active_key:
            return """> [!WARNING]
> **Gemini API Key Missing**: A valid Gemini API Key is required to perform real-time web-grounded News, Sentiment, and Voice of Customer analysis. Please configure your key in the sidebar.
"""

        prompt = f"""
You are an expert, institutional-grade market sentiment analyst writing an investment memo.
Perform a detailed, web-grounded news, customer sentiment, and social media sentiment analysis for {company_name} (Ticker: {ticker}) in the {industry} industry.

Your response must be a detailed investment memo section addressing:
1. **Major News Updates**: Aggregate and summarize the most significant recent news updates about the company. Reference coverage from top business news channels (e.g. CNBC, Bloomberg, Reuters, Financial Times, Wall Street Journal).
2. **Customer Sentiments (Voice of Customers)**: Search for and summarize what actual customers are saying about the company's products/services (reliability, quality, user satisfaction, customer service).
3. **Social Media & Retail Sentiment**: Summarize what top financial social media channels, retail investor forums (like Reddit, Twitter/X, and financial blogs), and major local financial influencers in the country/industry are saying about this company.

Please structure the memo using professional investment banking layout (Markdown format) with clear headers, quotes or summaries, and bullet points. Do not use generic placeholders.
"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={active_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "tools": [
                    {"google_search": {}}
                ]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            else:
                return f"""> [!ERROR]
> **Gemini API Request Failed (Status {response.status_code})**: Unable to complete news and sentiment analysis.
> Details: {response.text}
"""
        except Exception as e:
            return f"""> [!ERROR]
> **Connection Error**: Failed to request Gemini API.
> Details: {e}
"""
