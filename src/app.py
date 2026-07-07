import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import time

from data_fetcher import DataFetcher
from agents.metrics_agent import MetricsAgent
from agents.valuation_agent import ValuationAgent
from agents.risk_agent import RiskAgent
from agents.report_agent import ReportAgent
from agents.competitive_landscape_agent import CompetitiveLandscapeAgent
from agents.news_sentiment_agent import NewsSentimentAgent
from agents.major_risks_agent import MajorRisksAgent
from agents.company_overview_agent import CompanyOverviewAgent
from agents.macro_outlook_agent import MacroOutlookAgent
from agents.industry_analysis_agent import IndustryAnalysisAgent
from agents.performance_assessor_agent import PerformanceAssessorAgent

# --- Helper to parse JSON-structured agent sections ---
def parse_agent_sections(raw_text: str):
    if not raw_text or raw_text.strip().startswith(">"):
        return [{"section": "Status / Alert", "summary": "Sub-agent status message", "details": raw_text}]
        
    cleaned = raw_text.strip()
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace:last_brace+1]
        
    try:
        data = json.loads(cleaned)
        sections = []
        raw_sections = data.get("sections", [])
        for sec in raw_sections:
            sections.append({
                "section": sec.get("section_name", "Analysis Section"),
                "summary": sec.get("summary", "Summary of findings"),
                "details": sec.get("details", "")
            })
        return sections
    except Exception:
        # Fallback if no JSON format exists
        summary_limit = 150
        summary_txt = raw_text[:summary_limit].strip()
        if len(raw_text) > summary_limit:
            summary_txt += "..."
        return [{"section": "Analysis Overview", "summary": summary_txt, "details": raw_text}]

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="AI Stock Investment Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Custom CSS styling for premium SaaS look & feel ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');
    
    /* 1. Global Light Theme Override (Monochrome Base) */
    .stApp {
        background-color: #FFFFFF !important;
        color: #111111 !important;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling: Minimalist off-white with thin border */
    section[data-testid="stSidebar"] {
        background-color: #F9FAFB !important;
        border-right: 1px solid #E5E7EB !important;
    }
    section[data-testid="stSidebar"] * {
        color: #111111 !important;
    }
    section[data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #111111 !important;
        border: 1px solid #D1D5DB !important;
    }

    /* Branded headers */
    h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] h3 {
        color: #111111 !important;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    /* 2. Bold Typography and Title */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #111111;
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.03em;
        margin-bottom: 0.1rem;
    }
    
    .sub-title {
        font-size: 1.1rem;
        color: #0052FF;
        font-weight: 600;
        letter-spacing: -0.01em;
        margin-bottom: 2.2rem;
    }
    
    /* 3. Grid-Based Minimalist Cards with Electric Blue hover */
    .saas-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 1.5rem;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1.2rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .saas-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0, 82, 255, 0.06);
        border-color: #0052FF;
    }
    
    .card-header-badge {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #0052FF;
        background-color: #E6EEFF;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        margin-bottom: 0.6rem;
        border: 1px solid rgba(0, 82, 255, 0.15);
    }
    
    .card-section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111111;
        font-family: 'Outfit', sans-serif;
        margin-bottom: 0.6rem;
    }
    
    .card-summary-text {
        font-size: 0.95rem;
        color: #4B5563;
        line-height: 1.6;
        margin-bottom: 1.2rem;
    }
    
    /* Left Border highlights styled as Electric Blue */
    .saas-metric, .saas-metric-coral, .saas-metric-yellow {
        background: #FFFFFF;
        border-left: 4px solid #0052FF !important;
    }
    
    /* Core Parameter Cards */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        border: 1px solid #E5E7EB;
        text-align: center;
        transition: all 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 82, 255, 0.05);
        border-color: #0052FF;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #4B5563;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
        letter-spacing: 0.03em;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0052FF;
    }
    
    /* Analyst Research Memo Card */
    .report-card {
        background-color: #FAFAFA;
        border-left: 5px solid #0052FF;
        border-radius: 6px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border-top: 1px solid #E5E7EB;
        border-right: 1px solid #E5E7EB;
        border-bottom: 1px solid #E5E7EB;
        margin-top: 1.5rem;
        color: #111111;
    }
    .report-card * {
        color: #111111 !important;
    }
    
    /* Streamlit Tabs Custom Design */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F3F4F6 !important;
        border-radius: 8px !important;
        padding: 4px !important;
        border: 1px solid #E5E7EB !important;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem;
        font-weight: 600;
        color: #4B5563 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #FFFFFF !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #0052FF !important;
    }
    .stTabs [data-baseweb="tab-list"] button:hover [data-testid="stMarkdownContainer"] p {
        color: #111111 !important;
    }
    
    /* Dataframes styles */
    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Disk Cache Helpers for Free Tier stability ---
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def load_disk_cache(ticker: str):
    path = os.path.join(CACHE_DIR, f"{ticker.upper()}_cache.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_disk_cache(ticker: str, data: dict):
    serializable = {}
    for k, v in data.items():
        if isinstance(v, str) and not any(ind in v for ind in ["### API Error", "### Gemini API Limit Reached", "### Connection Exception", "Status 429", "Request Failed", "Key Missing"]):
            serializable[k] = v
    if serializable:
        path = os.path.join(CACHE_DIR, f"{ticker.upper()}_cache.json")
        try:
            with open(path, "w") as f:
                json.dump(serializable, f, indent=4)
        except Exception:
            pass

# --- 3. Sidebar Configuration ---
st.sidebar.markdown("## Configuration Panel")
ticker_input = st.sidebar.text_input("Enter Stock Ticker", value="AAPL").upper().strip()

if st.sidebar.button("🧹 Clear Ticker Disk Cache", use_container_width=True):
    if ticker_input:
        path = os.path.join(CACHE_DIR, f"{ticker_input.upper()}_cache.json")
        if os.path.exists(path):
            os.remove(path)
        st.session_state.pop("agent_cache", None)
        st.session_state.pop("cached_ticker", None)
        st.success(f"Cleared cache for {ticker_input}!")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### API Credentials")
api_key_input = st.sidebar.text_input("Gemini API Key (Optional)", type="password", help="If left blank, the app will try to read from local environment variables or .env file.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Valuation Settings")
rf_rate = st.sidebar.slider("Risk-Free Rate (Rf)", min_value=0.01, max_value=0.08, value=0.045, step=0.001, format="%.3f")
market_ret = st.sidebar.slider("Expected Market Return (Rm)", min_value=0.05, max_value=0.15, value=0.10, step=0.005)
growth_proj = st.sidebar.slider("FCF Growth (5-Yr)", min_value=-0.10, max_value=0.30, value=0.06, step=0.01)

# Initialize Agents
metrics_agent = MetricsAgent()
valuation_agent = ValuationAgent()
risk_agent = RiskAgent()
report_agent = ReportAgent()
comp_landscape_agent = CompetitiveLandscapeAgent()
news_sentiment_agent = NewsSentimentAgent()
major_risks_agent = MajorRisksAgent()
company_overview_agent = CompanyOverviewAgent()
macro_outlook_agent = MacroOutlookAgent()
industry_analysis_agent = IndustryAnalysisAgent()
performance_assessor_agent = PerformanceAssessorAgent()

# --- 4. Main App Flow ---
st.markdown('<div class="main-title">AI Investment Analyst</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Smart Insights, Real-Time Analysis</div>', unsafe_allow_html=True)

if ticker_input:
    # Initialize cache for qualitative agent outputs
    if "agent_cache" not in st.session_state or st.session_state.get("cached_ticker") != ticker_input:
        disk_cache = load_disk_cache(ticker_input)
        st.session_state["agent_cache"] = disk_cache
        st.session_state["cached_ticker"] = ticker_input

    # Clear any "API Key Missing" warnings if the user has now provided an API key in the sidebar
    active_key = api_key_input.strip() if api_key_input.strip() else None
    current_key_state = active_key if active_key else "None"
    if "cached_api_key" not in st.session_state or st.session_state.get("cached_api_key") != current_key_state:
        if "agent_cache" in st.session_state:
            for k in list(st.session_state["agent_cache"].keys()):
                val = st.session_state["agent_cache"][k]
                if isinstance(val, str) and "Key Missing" in val:
                    st.session_state["agent_cache"].pop(k)
        st.session_state["cached_api_key"] = current_key_state

    # 4.1 Ingest Data
    with st.spinner(f"Aggregating market data for {ticker_input}..."):
        fetcher = DataFetcher(ticker_input)
        info = fetcher.get_info()
        hist = fetcher.get_historical_prices(period="1y")
        financials = fetcher.get_financial_statements()

    if hist.empty:
        st.error(f"Could not retrieve stock data for ticker '{ticker_input}'. Please check the symbol and try again.")
    else:
        # Display Company Summary header
        company_name = info.get("shortName", ticker_input)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose") or 0.0
        currency = info.get("currency", "USD")

        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader(f"{company_name} ({ticker_input})")
            st.caption(f"Sector: **{sector}** | Industry: **{industry}**")
        with col_right:
            st.markdown(f"<div style='text-align: right;'><span style='font-size: 2.2rem; font-weight: 700;'>${current_price:.2f}</span> <span style='font-size: 1.1rem; color: #7f8c8d;'>{currency}</span></div>", unsafe_allow_html=True)

        # --- Run all qualitative sub-agents up front ---
        active_key = api_key_input.strip() if api_key_input.strip() else None
        
        with st.status(f"🚀 Running Multi-Agent Stock Analysis for {company_name}...", expanded=True) as status:
            if "agent_1" not in st.session_state["agent_cache"]:
                st.write("🏢 Agent 1: Compiling company overview and corporate profile...")
                st.session_state["agent_cache"]["agent_1"] = company_overview_agent.analyze_company_overview(
                    active_key, company_name, ticker_input, sector, industry
                )
                save_disk_cache(ticker_input, st.session_state["agent_cache"])
                time.sleep(4)
            if "agent_2" not in st.session_state["agent_cache"]:
                st.write("🌍 Agent 2: Analyzing macroeconomic conditions and sector trends...")
                st.session_state["agent_cache"]["agent_2"] = macro_outlook_agent.analyze_macro_outlook(
                    active_key, company_name, ticker_input, sector, industry
                )
                save_disk_cache(ticker_input, st.session_state["agent_cache"])
                time.sleep(4)
            if "agent_3" not in st.session_state["agent_cache"]:
                st.write("🤝 Agent 3: Assessing competitive moats and market landscape...")
                st.session_state["agent_cache"]["agent_3"] = comp_landscape_agent.analyze_competitive_landscape(
                    active_key, company_name, ticker_input, sector, industry
                )
                save_disk_cache(ticker_input, st.session_state["agent_cache"])
                time.sleep(4)
            if "agent_4" not in st.session_state["agent_cache"]:
                st.write("📣 Agent 4: Scanning news articles and social media sentiment...")
                st.session_state["agent_cache"]["agent_4"] = news_sentiment_agent.analyze_news_and_sentiment(
                    active_key, company_name, ticker_input, industry
                )
                save_disk_cache(ticker_input, st.session_state["agent_cache"])
                time.sleep(4)
            if "agent_5" not in st.session_state["agent_cache"]:
                st.write("📊 Agent 5: Evaluating industry growth dynamics...")
                st.session_state["agent_cache"]["agent_5"] = industry_analysis_agent.analyze_industry(
                    active_key, company_name, ticker_input, sector, industry
                )
                save_disk_cache(ticker_input, st.session_state["agent_cache"])
                time.sleep(4)
            if "agent_6" not in st.session_state["agent_cache"]:
                st.write("🔍 Agent 6: Scoring financial and operational performance benchmarks...")
                st.session_state["agent_cache"]["agent_6"] = performance_assessor_agent.analyze_performance(
                    active_key, company_name
                )
                save_disk_cache(ticker_input, st.session_state["agent_cache"])
                time.sleep(4)
            if "agent_7" not in st.session_state["agent_cache"]:
                st.write("🔥 Agent 7: Assessing operational, financial, and GRC risks...")
                st.session_state["agent_cache"]["agent_7"] = major_risks_agent.analyze_major_risks(
                    active_key, company_name, ticker_input
                )
                save_disk_cache(ticker_input, st.session_state["agent_cache"])
            status.update(label="Analysis complete! All qualitative reports loaded.", state="complete", expanded=False)

        # Tabs for Dashboard Layout
        tab_report, tab_company_overview, tab_macro_outlook, tab_comp, tab_sentiment, tab_industry_analysis, tab_performance_assessor, tab_major_risks = st.tabs([
            "📋 Master Research Report", 
            "🏢 Agent 1: Company Overview",
            "🌍 Agent 2: Macro Outlook",
            "🤝 Agent 3: Competitive Landscape",
            "📣 Agent 4: News & Sentiments",
            "📊 Agent 5: Industry Analysis",
            "🔍 Agent 6: Performance Assessor",
            "🔥 Agent 7: Major Risks"
        ])

        # --- Tab 1: AI Generated Report ---
        with tab_report:
            st.subheader("AI Investment Analyst Report")
            
            # Compute underlying data for report context
            tech_df = metrics_agent.compute_technical_indicators(hist)
            latest_row = tech_df.iloc[-1] if not tech_df.empty else pd.Series()
            
            technical_summary = {
                "SMA_20": f"${latest_row.get('SMA_20', 0):.2f}" if 'SMA_20' in latest_row else "N/A",
                "SMA_50": f"${latest_row.get('SMA_50', 0):.2f}" if 'SMA_50' in latest_row else "N/A",
                "SMA_200": f"${latest_row.get('SMA_200', 0):.2f}" if 'SMA_200' in latest_row else "N/A",
                "RSI_14": f"{latest_row.get('RSI_14', 50):.2f}" if 'RSI_14' in latest_row else "N/A",
                "MACD": f"{latest_row.get('MACD', 0):.4f}" if 'MACD' in latest_row else "N/A",
                "MACD_Signal": f"{latest_row.get('MACD_Signal', 0):.4f}" if 'MACD_Signal' in latest_row else "N/A"
            }
            
            fundamental_summary = metrics_agent.compute_fundamental_metrics(info, financials)
            
            valuation_dcf = valuation_agent.run_dcf_valuation(
                info, financials, 
                risk_free_rate=rf_rate, 
                market_return=market_ret, 
                growth_rate=growth_proj
            )
            valuation_multiples = valuation_agent.run_multiples_valuation(info)
            valuation_summary = {
                "intrinsic_value": valuation_dcf.get("intrinsic_value"),
                "calculated_wacc": valuation_dcf.get("calculated_wacc"),
                "fcf_projections": valuation_dcf.get("fcf_projections"),
                "target_price": valuation_multiples.get("target_price"),
                "multiple_used": valuation_multiples.get("multiple_used")
            }
            
            risk_summary = risk_agent.analyze_risk(hist, info)

            # Compile available qualitative sub-agent reports
            qualitative_reports = {
                "Company Overview": st.session_state["agent_cache"].get("agent_1", ""),
                "Macro Outlook": st.session_state["agent_cache"].get("agent_2", ""),
                "Competitive Landscape": st.session_state["agent_cache"].get("agent_3", ""),
                "News & Sentiments": st.session_state["agent_cache"].get("agent_4", ""),
                "Industry Analysis": st.session_state["agent_cache"].get("agent_5", ""),
                "Performance Assessor": st.session_state["agent_cache"].get("agent_6", ""),
                "Major Risks": st.session_state["agent_cache"].get("agent_7", "")
            }

            # Generate or Retrieve Main Report (invalidates if math sliders or available qualitative sub-agent outputs change)
            cached_agents_str = ",".join([k for k, v in qualitative_reports.items() if v])
            report_cache_key = f"{ticker_input}_{rf_rate:.4f}_{market_ret:.4f}_{growth_proj:.4f}_{api_key_input}_{cached_agents_str}"
            
            if "main_report" not in st.session_state["agent_cache"] or st.session_state.get("main_report_key") != report_cache_key:
                with st.spinner("Analyzing stock metrics and generating report..."):
                    active_key = api_key_input.strip() if api_key_input.strip() else None
                    report_agent.api_key = active_key or report_agent.api_key
                    st.session_state["agent_cache"]["main_report"] = report_agent.generate_report(
                        info, 
                        technical_summary, 
                        fundamental_summary, 
                        valuation_summary, 
                        risk_summary,
                        qualitative_reports=qualitative_reports
                    )
                    st.session_state["main_report_key"] = report_cache_key
            report_markdown = st.session_state["agent_cache"]["main_report"]
            
            # Check if there was an API or connection error
            is_error = False
            for err_indicator in ["### API Error", "### Gemini API Limit Reached", "### Connection Exception"]:
                if report_markdown.startswith(err_indicator):
                    is_error = True
                    break
            
            if is_error:
                st.warning("The Gemini API is currently experiencing a high volume of requests or has hit rate limits. A temporary rule-based fallback report is displayed below.")
                if st.button("🔄 Force Retry Analyst Report Generation", use_container_width=True):
                    st.session_state.pop("main_report_key", None)
                    st.session_state["agent_cache"].pop("main_report", None)
                    st.rerun()
            
            st.markdown(f'<div class="report-card">{report_markdown}</div>', unsafe_allow_html=True)
            
            # Nest quantitative sub-tabs directly in the Master Research Report tab
            st.markdown("<br><hr style='border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
            st.subheader("Quantitative Analytics & Valuations")
            quant_sub_tab_charts, quant_sub_tab_metrics, quant_sub_tab_valuation, quant_sub_tab_risk = st.tabs([
                "📈 Price & Technicals",
                "📊 Fundamental Metrics",
                "💎 Valuation Engine",
                "📊 Volatility & VaR"
            ])
            
            with quant_sub_tab_charts:
                st.subheader("Price History and Technical Signals")
                
                # Get data with technical metrics computed
                plot_df = metrics_agent.compute_technical_indicators(hist)
                
                # Create Plotly Chart
                fig = make_subplots(
                    rows=3, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.03,
                    row_heights=[0.6, 0.2, 0.2]
                )
                
                # Candlestick chart
                fig.add_trace(go.Candlestick(
                    x=plot_df.index,
                    open=plot_df['Open'],
                    high=plot_df['High'],
                    low=plot_df['Low'],
                    close=plot_df['Close'],
                    name="Stock Price"
                ), row=1, col=1)
                
                # Volume Chart
                fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['Volume'], name='Volume', marker=dict(color='blue')), row=2, col=1)
                
                # RSI
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['RSI_14'], name='RSI (14)', line=dict(color='green', width=1.2)), row=3, col=1)
                
                # RSI lines for thresholds (Overbought/Oversold)
                fig.add_shape(type="line", x0=plot_df.index[0], y0=70, x1=plot_df.index[-1], y1=70, line=dict(color="red", width=1, dash="dash"), row=3, col=1)
                fig.add_shape(type="line", x0=plot_df.index[0], y0=30, x1=plot_df.index[-1], y1=30, line=dict(color="green", width=1, dash="dash"), row=3, col=1)
    
                fig.update_layout(
                    height=700, 
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=10, r=10, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color='#111111')
                )
                fig.update_xaxes(gridcolor='#E5E7EB', color='#4B5563')
                fig.update_yaxes(gridcolor='#E5E7EB', color='#4B5563')
    
                st.plotly_chart(fig, use_container_width=True)
                
            with quant_sub_tab_metrics:
                st.subheader("Fundamental Financial Ratios")
                
                fm = fundamental_summary
                
                # Dynamic Columns for metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.markdown(f"<div class='metric-card'><div class='metric-label'>P/E Ratio</div><div class='metric-value'>{fm.get('pe_ratio', 'N/A')}</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='metric-card'><div class='metric-label'>P/B Ratio</div><div class='metric-value'>{fm.get('pb_ratio', 'N/A')}</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div class='metric-card'><div class='metric-label'>Profit Margin</div><div class='metric-value'>{fm.get('profit_margin', 'N/A')}</div></div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div class='metric-card'><div class='metric-label'>ROE</div><div class='metric-value'>{fm.get('roe', 'N/A')}</div></div>", unsafe_allow_html=True)
                with col5:
                    st.markdown(f"<div class='metric-card'><div class='metric-label'>Debt to Equity</div><div class='metric-value'>{fm.get('debt_to_equity', 'N/A')}</div></div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("Business Summary")
                    st.write(info.get("longBusinessSummary", "No description available."))
                with col_right:
                    st.subheader("Key Statistics")
                    df_stats = pd.DataFrame([
                        {"Key": "Beta", "Value": f"{info.get('beta'):.2f}" if info.get('beta') is not None else "N/A"},
                        {"Key": "Dividend Yield", "Value": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A"},
                        {"Key": "Enterprise Value", "Value": f"${info.get('enterpriseValue', 0):,}" if info.get('enterpriseValue') else "N/A"},
                        {"Key": "Outstanding Shares", "Value": f"{info.get('sharesOutstanding', 0):,}" if info.get('sharesOutstanding') else "N/A"},
                        {"Key": "Market Cap", "Value": f"${info.get('marketCap', 0):,}" if info.get('marketCap') else "N/A"},
                    ])
                    st.dataframe(df_stats, hide_index=True, use_container_width=True)
                    
            with quant_sub_tab_valuation:
                st.subheader("Intrinsic Valuation Calculators")
                
                col_dcf, col_multi = st.columns(2)
                
                with col_dcf:
                    st.markdown("### Discounted Cash Flow (DCF)")
                    if valuation_dcf["status"] == "Success":
                        iv = valuation_dcf["intrinsic_value"]
                        wacc_val = valuation_dcf["calculated_wacc"]
                        fcf_proj = valuation_dcf["fcf_projections"]
                        
                        st.markdown(f"**DCF Intrinsic Value**: `${iv:.2f}`")
                        st.markdown(f"**Calculated WACC**: `{wacc_val*100:.2f}%`")
                        
                        st.markdown("#### Projected Free Cash Flows (5 Years)")
                        fcf_proj_df = pd.DataFrame({
                            "Year": [f"Year {i}" for i in range(1, len(fcf_proj) + 1)],
                            "Projected FCF": [f"${val:,.2f}" for val in fcf_proj]
                        })
                        st.dataframe(fcf_proj_df, hide_index=True, use_container_width=True)
                    else:
                        st.warning(f"DCF Engine status: {valuation_dcf['status']}")
                
                with col_multi:
                    st.markdown("### Comparable Multiples Valuation")
                    if valuation_multiples["status"] == "Success":
                        t_price = valuation_multiples["target_price"]
                        m_used = valuation_multiples["multiple_used"]
                        
                        st.markdown(f"**Multiples Target Price**: `${t_price:.2f}`")
                        st.markdown(f"**Peer P/E Multiple applied**: `{m_used:.1f}x`")
                        st.info("The target price is calculated by multiplying the trailing/forward earnings per share (EPS) by a sector/industry average multiple.")
                    else:
                        st.warning(f"Multiples Engine status: {valuation_multiples['status']}")
                        
            with quant_sub_tab_risk:
                st.subheader("Downside and Volatility Analysis")
                if risk_summary["status"] == "Success":
                    col_vol, col_var, col_beta, col_dd = st.columns(4)
                    
                    vol_val = f"{risk_summary['annualized_volatility']*100:.2f}%"
                    var_val = f"{risk_summary['var_95']*100:.2f}%"
                    beta_val = f"{risk_summary['beta']:.2f}" if risk_summary.get('beta') else "N/A"
                    dd_val = f"{risk_summary['max_drawdown']*100:.2f}%"
                    
                    col_vol.markdown(f"<div class='metric-card'><div class='metric-label'>Annual Volatility</div><div class='metric-value'>{vol_val}</div></div>", unsafe_allow_html=True)
                    col_var.markdown(f"<div class='metric-card'><div class='metric-label'>Value at Risk (95%)</div><div class='metric-value'>{var_val}</div></div>", unsafe_allow_html=True)
                    col_beta.markdown(f"<div class='metric-card'><div class='metric-label'>Beta Coefficient</div><div class='metric-value'>{beta_val}</div></div>", unsafe_allow_html=True)
                    col_dd.markdown(f"<div class='metric-card'><div class='metric-label'>Max Drawdown</div><div class='metric-value'>{dd_val}</div></div>", unsafe_allow_html=True)
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown("""
                    ### Risk Metric Explanations:
                    - **Annualized Volatility**: A statistical measure of the dispersion of returns for a given security. Higher volatility means higher price variance and risk.
                    - **Value at Risk (95% Daily)**: Represents the minimum expected percentage loss on any given single trading day at a 95% confidence level. E.g., if VaR is -3.5%, there is a 5% chance the stock declines more than 3.5% in a day.
                    - **Beta Coefficient**: Measures the volatility of the stock relative to the overall market (S&P 500). A beta of 1.0 means the stock moves with the market; >1.0 means more volatile; <1.0 means less volatile.
                    - **Max Drawdown**: The maximum historic peak-to-trough decline of the stock price over the past year.
                    """)
                else:
                    st.warning(f"Risk Engine status: {risk_summary['status']}")

        # --- Tab 1.1 (Agent 1): Company Overview ---
        with tab_company_overview:
            st.subheader("Agent 1: Company Overview Analysis")
            overview_markdown = st.session_state["agent_cache"].get("agent_1", "")
            if overview_markdown:
                sections = parse_agent_sections(overview_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Status / Alert":
                    st.markdown(f'<div class="saas-card saas-metric-coral">{overview_markdown}</div>', unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns(2)
                    for i, sec in enumerate(sections):
                        target_col = col1 if i % 2 == 0 else col2
                        with target_col:
                            highlight_class = "saas-metric" if i % 3 == 0 else ("saas-metric-coral" if i % 3 == 1 else "saas-metric-yellow")
                            st.markdown(f"""
                            <div class="saas-card {highlight_class}">
                                <div class="card-header-badge">Agent 1 Section {i+1}</div>
                                <div class="card-section-title">{sec['section']}</div>
                                <div class="card-summary-text">{sec['summary']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.popover(f"🔍 View {sec['section']} Details", use_container_width=True):
                                st.markdown(sec['details'])
                            st.write("")
            else:
                st.info("No data available for Agent 1.")

        # --- Tab 1.2 (Agent 2): Macro Outlook ---
        with tab_macro_outlook:
            st.subheader("Agent 2: Macroeconomic & Sector Outlook")
            macro_markdown = st.session_state["agent_cache"].get("agent_2", "")
            if macro_markdown:
                sections = parse_agent_sections(macro_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Status / Alert":
                    st.markdown(f'<div class="saas-card saas-metric-coral">{macro_markdown}</div>', unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns(2)
                    for i, sec in enumerate(sections):
                        target_col = col1 if i % 2 == 0 else col2
                        with target_col:
                            highlight_class = "saas-metric-coral" if i % 3 == 0 else ("saas-metric-yellow" if i % 3 == 1 else "saas-metric")
                            st.markdown(f"""
                            <div class="saas-card {highlight_class}">
                                <div class="card-header-badge">Agent 2 Section {i+1}</div>
                                <div class="card-section-title">{sec['section']}</div>
                                <div class="card-summary-text">{sec['summary']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.popover(f"🔍 View {sec['section']} Details", use_container_width=True):
                                st.markdown(sec['details'])
                            st.write("")
            else:
                st.info("No data available for Agent 2.")

        # --- Tab 3: Agent 3: Competitive Landscape ---
        with tab_comp:
            st.subheader("Agent 3: Competitive Landscape Analysis")
            comp_markdown = st.session_state["agent_cache"].get("agent_3", "")
            if comp_markdown:
                sections = parse_agent_sections(comp_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Status / Alert":
                    st.markdown(f'<div class="saas-card saas-metric-coral">{comp_markdown}</div>', unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns(2)
                    for i, sec in enumerate(sections):
                        target_col = col1 if i % 2 == 0 else col2
                        with target_col:
                            highlight_class = "saas-metric" if i % 3 == 0 else ("saas-metric-coral" if i % 3 == 1 else "saas-metric-yellow")
                            st.markdown(f"""
                            <div class="saas-card {highlight_class}">
                                <div class="card-header-badge">Agent 3 Section {i+1}</div>
                                <div class="card-section-title">{sec['section']}</div>
                                <div class="card-summary-text">{sec['summary']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.popover(f"🔍 View {sec['section']} Details", use_container_width=True):
                                st.markdown(sec['details'])
                            st.write("")
            else:
                st.info("No data available for Agent 3.")

        # --- Tab 4: Agent 4: News & Sentiments ---
        with tab_sentiment:
            st.subheader("Agent 4: News, Sentiments, and Voice of Customers")
            sentiment_markdown = st.session_state["agent_cache"].get("agent_4", "")
            if sentiment_markdown:
                sections = parse_agent_sections(sentiment_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Status / Alert":
                    st.markdown(f'<div class="saas-card saas-metric-coral">{sentiment_markdown}</div>', unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns(2)
                    for i, sec in enumerate(sections):
                        target_col = col1 if i % 2 == 0 else col2
                        with target_col:
                            highlight_class = "saas-metric-yellow" if i % 3 == 0 else ("saas-metric" if i % 3 == 1 else "saas-metric-coral")
                            st.markdown(f"""
                            <div class="saas-card {highlight_class}">
                                <div class="card-header-badge">Agent 4 Section {i+1}</div>
                                <div class="card-section-title">{sec['section']}</div>
                                <div class="card-summary-text">{sec['summary']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.popover(f"🔍 View {sec['section']} Details", use_container_width=True):
                                st.markdown(sec['details'])
                            st.write("")
            else:
                st.info("No data available for Agent 4.")

        # --- Tab 5: Agent 5: Industry Analysis ---
        with tab_industry_analysis:
            st.subheader("Agent 5: Industry & Market Analysis")
            industry_markdown = st.session_state["agent_cache"].get("agent_5", "")
            if industry_markdown:
                sections = parse_agent_sections(industry_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Status / Alert":
                    st.markdown(f'<div class="saas-card saas-metric-coral">{industry_markdown}</div>', unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns(2)
                    for i, sec in enumerate(sections):
                        target_col = col1 if i % 2 == 0 else col2
                        with target_col:
                            highlight_class = "saas-metric-yellow" if i % 3 == 0 else ("saas-metric" if i % 3 == 1 else "saas-metric-coral")
                            st.markdown(f"""
                            <div class="saas-card {highlight_class}">
                                <div class="card-header-badge">Agent 5 Section {i+1}</div>
                                <div class="card-section-title">{sec['section']}</div>
                                <div class="card-summary-text">{sec['summary']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.popover(f"🔍 View {sec['section']} Details", use_container_width=True):
                                st.markdown(sec['details'])
                            st.write("")
            else:
                st.info("No data available for Agent 5.")

        # --- Tab 6: Agent 6: Performance Assessor ---
        with tab_performance_assessor:
            st.subheader("Agent 6: Financial & Operational Performance Assessment")
            perf_markdown = st.session_state["agent_cache"].get("agent_6", "")
            if perf_markdown:
                # Render JSON section format if valid, else fallback to raw markdown rendering
                if perf_markdown and not perf_markdown.strip().startswith(">"):
                    try:
                        cleaned_perf = perf_markdown.strip()
                        first_brace = cleaned_perf.find('{')
                        last_brace = cleaned_perf.rfind('}')
                        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                            cleaned_perf = cleaned_perf[first_brace:last_brace+1]
                        data = json.loads(cleaned_perf)
                        for sec in data.get("sections", []):
                            st.markdown(f"### {sec.get('section_name')}")
                            st.markdown(f"*{sec.get('summary')}*")
                            st.markdown(sec.get('details'))
                            st.markdown("---")
                    except Exception:
                        st.markdown(f'<div class="report-card">{perf_markdown}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(perf_markdown, unsafe_allow_html=True)
            else:
                st.info("No data available for Agent 6.")



        # --- Tab: Agent 7: Major Risks ---
        with tab_major_risks:
            st.subheader("Agent 7: Qualitative Risk Assessment")
            major_risks_markdown = st.session_state["agent_cache"].get("agent_7", "")
            if major_risks_markdown:
                sections = parse_agent_sections(major_risks_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Status / Alert":
                    st.markdown(f'<div class="saas-card saas-metric-coral">{major_risks_markdown}</div>', unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns(2)
                    for i, sec in enumerate(sections):
                        target_col = col1 if i % 2 == 0 else col2
                        with target_col:
                            highlight_class = "saas-metric-coral" if i % 3 == 0 else ("saas-metric-yellow" if i % 3 == 1 else "saas-metric")
                            st.markdown(f"""
                            <div class="saas-card {highlight_class}">
                                <div class="card-header-badge">Agent 7 Section {i+1}</div>
                                <div class="card-section-title">{sec['section']}</div>
                                <div class="card-summary-text">{sec['summary']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.popover(f"🔍 View {sec['section']} Details", use_container_width=True):
                                st.markdown(sec['details'])
                            st.write("")
            else:
                st.info("No data available for Agent 7.")

else:
    st.info("Enter a stock ticker in the sidebar to begin analysis.")
