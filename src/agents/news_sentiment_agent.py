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

You MUST structure your response strictly into 3 sections:
1. Major News Updates
2. Customer Sentiments
3. Social Media & Retail Sentiment

For each section, you MUST format the output exactly as follows using the exact delimiter tags:

===SECTION===
[Section Name]
===SUMMARY===
[A concise, 1-2 sentence overall summary/headline of the section]
===DETAILS===
[A detailed, institutional-grade, verbose markdown analysis with bullet points, quotes, and paragraphs containing the deep research]

Analyze the following for each section:
1. **Major News Updates**: Aggregate and summarize the most significant recent news updates about the company. Reference coverage from top business news channels (e.g. CNBC, Bloomberg, Reuters, Financial Times, Wall Street Journal).
2. **Customer Sentiments**: Search for and summarize what actual customers are saying about the company's products/services (reliability, quality, user satisfaction, customer service).
3. **Social Media & Retail Sentiment**: Summarize what top financial social media channels, retail investor forums (like Reddit, Twitter/X, and financial blogs), and major local financial influencers in the country/industry are saying about this company.
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
            elif response.status_code == 429:
                return """> [!WARNING]
> **Gemini API Limit Reached (Status 429)**: You have exceeded the request quota limit for the Gemini Free Tier.
> 
> * **If you generated a new API key recently**: Make sure you have added a billing account to your Google AI Studio project to enable higher rate limits.
> * **Temporary Delay**: The Free Tier limits requests per minute. Please wait 1-2 minutes and toggle this agent ON again to retry.
> """
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
