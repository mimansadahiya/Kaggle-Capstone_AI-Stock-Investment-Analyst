import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from data_fetcher import DataFetcher
from agents.metrics_agent import MetricsAgent
from agents.valuation_agent import ValuationAgent
from agents.risk_agent import RiskAgent
from agents.report_agent import ReportAgent
from agents.competitive_landscape_agent import CompetitiveLandscapeAgent
from agents.news_sentiment_agent import NewsSentimentAgent
from agents.major_risks_agent import MajorRisksAgent

# --- Helper to parse delimiter-separated agent sections ---
def parse_agent_sections(raw_text: str):
    if "===SECTION===" not in raw_text:
        # Fallback if no delimiter markers exist
        summary_limit = 150
        summary_txt = raw_text[:summary_limit].strip()
        if len(raw_text) > summary_limit:
            summary_txt += "..."
        return [{"section": "Analysis Overview", "summary": summary_txt, "details": raw_text}]
    
    sections = []
    parts = raw_text.split("===SECTION===")
    for part in parts:
        if not part.strip():
            continue
        try:
            sec_parts = part.split("===SUMMARY===")
            section_name = sec_parts[0].strip()
            
            rem_parts = sec_parts[1].split("===DETAILS===")
            summary = rem_parts[0].strip()
            details = rem_parts[1].strip()
            
            sections.append({
                "section": section_name,
                "summary": summary,
                "details": details
            })
        except Exception:
            sections.append({
                "section": "Analysis Section",
                "summary": "Detailed research report notes.",
                "details": part
            })
    return sections

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        font-size: 2.7rem;
        font-weight: 700;
        color: #475C7A;
        font-family: 'Outfit', sans-serif;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        font-size: 1.05rem;
        color: #685D79;
        font-weight: 400;
        margin-bottom: 1.8rem;
    }
    
    /* SaaS Card Design system */
    .saas-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        margin-bottom: 1.2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .saas-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(71, 92, 122, 0.08), 0 4px 6px -2px rgba(71, 92, 122, 0.04);
        border-color: #AB6C82;
    }
    
    .card-header-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #475C7A;
        background-color: #f1f5f9;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        margin-bottom: 0.6rem;
        border: 1px solid #e2e8f0;
    }
    
    .card-section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #475C7A;
        font-family: 'Outfit', sans-serif;
        margin-bottom: 0.6rem;
    }
    
    .card-summary-text {
        font-size: 0.95rem;
        color: #4b5563;
        line-height: 1.5;
        margin-bottom: 1.2rem;
    }
    
    /* Custom highlights for metric cards */
    .saas-metric {
        background: linear-gradient(135deg, #ffffff 0%, #fcfbfb 100%);
        border-left: 4px solid #AB6C82;
    }
    .saas-metric-coral {
        background: linear-gradient(135deg, #ffffff 0%, #fcfbfb 100%);
        border-left: 4px solid #D8737F;
    }
    .saas-metric-yellow {
        background: linear-gradient(135deg, #ffffff 0%, #fcfbfb 100%);
        border-left: 4px solid #FCBB6D;
    }
    
    /* Keep metric cards for core parameters */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        border-color: #AB6C82;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #685D79;
        font-weight: 500;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #475C7A;
    }
    
    .report-card {
        background-color: #ffffff;
        border-left: 5px solid #475C7A;
        border-radius: 8px;
        padding: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        border-top: 1px solid #f1f3f5;
        border-right: 1px solid #f1f3f5;
        border-bottom: 1px solid #f1f3f5;
        margin-top: 1.5rem;
    }
    
    /* Tabs custom highlight */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem;
        font-weight: 600;
        color: #685D79;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom-color: #AB6C82 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Sidebar Configuration ---
st.sidebar.markdown("## Configuration Panel")
ticker_input = st.sidebar.text_input("Enter Stock Ticker", value="AAPL").upper().strip()

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

# --- 4. Main App Flow ---
st.markdown('<div class="main-title">AI Stock Investment Analyst</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Institutional-grade stock research reports powered by multi-agent analysis.</div>', unsafe_allow_html=True)

if ticker_input:
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

        # Tabs for Dashboard Layout
        tab_report, tab_charts, tab_metrics, tab_valuation, tab_comp, tab_sentiment, tab_risk_vol, tab_major_risks = st.tabs([
            "📋 Research Report", 
            "📈 Price & Technicals", 
            "📊 Fundamental Metrics", 
            "💎 Valuation Engine", 
            "🤝 Agent 3: Competitive Landscape",
            "📣 Agent 4: News & Sentiments",
            "📊 Volatility & VaR",
            "🔥 Agent 8: Major Risks"
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

            # Generate Report
            with st.spinner("Analyzing stock metrics and generating report..."):
                active_key = api_key_input.strip() if api_key_input.strip() else None
                report_agent.api_key = active_key or report_agent.api_key
                report_markdown = report_agent.generate_report(
                    info, 
                    technical_summary, 
                    fundamental_summary, 
                    valuation_summary, 
                    risk_summary
                )
            
            st.markdown(f'<div class="report-card">{report_markdown}</div>', unsafe_allow_html=True)

        # --- Tab 2: Interactive Charts ---
        with tab_charts:
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
            
            # Moving averages
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA_20'], name='SMA 20', line=dict(color='blue', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA_50'], name='SMA 50', line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA_200'], name='SMA 200', line=dict(color='red', width=1.2)), row=1, col=1)
            
            # MACD
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MACD'], name='MACD', line=dict(color='purple', width=1)), row=2, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MACD_Signal'], name='Signal', line=dict(color='grey', width=1)), row=2, col=1)
            fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['MACD_Hist'], name='Hist', marker_color='lightblue'), row=2, col=1)
            
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
                plot_bgcolor="rgba(0,0,0,0)"
            )
            fig.update_xaxes(gridcolor='#f1f3f5')
            fig.update_yaxes(gridcolor='#f1f3f5')

            st.plotly_chart(fig, use_container_width=True)

        # --- Tab 3: Fundamental Metrics ---
        with tab_metrics:
            st.subheader("Fundamental Financial Ratios")
            
            fm = fundamental_summary
            
            # Dynamic Columns for metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            pe_val = f"{fm['pe_ratio']:.2f}" if fm.get('pe_ratio') else "N/A"
            pb_val = f"{fm['pb_ratio']:.2f}" if fm.get('pb_ratio') else "N/A"
            margin_val = f"{fm['profit_margin']*100:.2f}%" if fm.get('profit_margin') else "N/A"
            roe_val = f"{fm['roe']*100:.2f}%" if fm.get('roe') else "N/A"
            de_val = f"{fm['debt_to_equity']:.2f}" if fm.get('debt_to_equity') else "N/A"

            col1.markdown(f"<div class='metric-card'><div class='metric-label'>P/E Ratio</div><div class='metric-value'>{pe_val}</div></div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='metric-card'><div class='metric-label'>P/B Ratio</div><div class='metric-value'>{pb_val}</div></div>", unsafe_allow_html=True)
            col3.markdown(f"<div class='metric-card'><div class='metric-label'>Profit Margin</div><div class='metric-value'>{margin_val}</div></div>", unsafe_allow_html=True)
            col4.markdown(f"<div class='metric-card'><div class='metric-label'>Return on Equity</div><div class='metric-value'>{roe_val}</div></div>", unsafe_allow_html=True)
            col5.markdown(f"<div class='metric-card'><div class='metric-label'>Debt to Equity</div><div class='metric-value'>{de_val}</div></div>", unsafe_allow_html=True)

            st.markdown("<br><br>", unsafe_allow_html=True)
            
            col_desc, col_state = st.columns([3, 2])
            with col_desc:
                st.subheader("Business Summary")
                st.write(info.get("longBusinessSummary", "No description available."))
            with col_state:
                st.subheader("Key Statistics")
                df_stats = pd.DataFrame([
                    {"Key": "Beta", "Value": f"{info.get('beta'):.2f}" if info.get('beta') is not None else "N/A"},
                    {"Key": "Dividend Yield", "Value": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A"},
                    {"Key": "Enterprise Value", "Value": f"${info.get('enterpriseValue', 0):,}" if info.get('enterpriseValue') else "N/A"},
                    {"Key": "Outstanding Shares", "Value": f"{info.get('sharesOutstanding', 0):,}" if info.get('sharesOutstanding') else "N/A"},
                    {"Key": "Market Cap", "Value": f"${info.get('marketCap', 0):,}" if info.get('marketCap') else "N/A"},
                ])
                st.dataframe(df_stats, hide_index=True, use_container_width=True)

        # --- Tab 4: Valuation Engine ---
        with tab_valuation:
            st.subheader("Intrinsic Valuation Calculators")
            
            col_dcf, col_multi = st.columns(2)
            
            with col_dcf:
                st.markdown("### Discounted Cash Flow (DCF)")
                if valuation_dcf["status"] == "Success":
                    iv = valuation_dcf["intrinsic_value"]
                    wacc_val = valuation_dcf["calculated_wacc"]
                    
                    st.markdown(f"**DCF Intrinsic Value Per Share**: `${iv:.2f}`")
                    st.markdown(f"**Cost of Equity (WACC used)**: `{wacc_val*100:.2f}%`")
                    
                    st.markdown("#### Projected Free Cash Flows (5 Years)")
                    fcf_proj_df = pd.DataFrame({
                        "Year": [f"Year {i}" for i in range(1, 6)],
                        "Projected FCF": [f"${val:,.2f}" for val in valuation_dcf["fcf_projections"]]
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

        # --- Tab: Volatility & VaR ---
        with tab_risk_vol:
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

        # --- Tab: Agent 3: Competitive Landscape ---
        with tab_comp:
            st.subheader("Agent 3: Competitive Landscape Analysis")
            run_agent_3 = st.toggle("Activate Agent 3 (Competitive Landscape)", value=False, key="run_agent_3")
            if run_agent_3:
                active_key = api_key_input.strip() if api_key_input.strip() else None
                with st.spinner("Analyzing competitive landscape..."):
                    comp_markdown = comp_landscape_agent.analyze_competitive_landscape(
                        active_key, company_name, ticker_input, sector, industry
                    )
                
                sections = parse_agent_sections(comp_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Analysis Overview":
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
                st.info("Agent 3 is currently inactive. Turn on the toggle switch above to run the analysis.")

        # --- Tab: Agent 4: News & Sentiments ---
        with tab_sentiment:
            st.subheader("Agent 4: News, Sentiments, and Voice of Customers")
            run_agent_4 = st.toggle("Activate Agent 4 (News & Sentiments)", value=False, key="run_agent_4")
            if run_agent_4:
                active_key = api_key_input.strip() if api_key_input.strip() else None
                with st.spinner("Analyzing recent news and market sentiment..."):
                    sentiment_markdown = news_sentiment_agent.analyze_news_and_sentiment(
                        active_key, company_name, ticker_input, industry
                    )
                
                sections = parse_agent_sections(sentiment_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Analysis Overview":
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
                st.info("Agent 4 is currently inactive. Turn on the toggle switch above to run the analysis.")

        # --- Tab: Agent 8: Major Risks ---
        with tab_major_risks:
            st.subheader("Agent 8: Qualitative Risk Assessment")
            run_agent_8 = st.toggle("Activate Agent 8 (Major Risks)", value=False, key="run_agent_8")
            if run_agent_8:
                active_key = api_key_input.strip() if api_key_input.strip() else None
                with st.spinner("Analyzing strategic, operational, financial, and GRC risk factors..."):
                    major_risks_markdown = major_risks_agent.analyze_major_risks(
                        active_key, company_name, ticker_input
                    )
                
                sections = parse_agent_sections(major_risks_markdown)
                if len(sections) == 1 and sections[0]["section"] == "Analysis Overview":
                    st.markdown(f'<div class="saas-card saas-metric-coral">{major_risks_markdown}</div>', unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns(2)
                    for i, sec in enumerate(sections):
                        target_col = col1 if i % 2 == 0 else col2
                        with target_col:
                            highlight_class = "saas-metric-coral" if i % 3 == 0 else ("saas-metric-yellow" if i % 3 == 1 else "saas-metric")
                            st.markdown(f"""
                            <div class="saas-card {highlight_class}">
                                <div class="card-header-badge">Agent 8 Section {i+1}</div>
                                <div class="card-section-title">{sec['section']}</div>
                                <div class="card-summary-text">{sec['summary']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            with st.popover(f"🔍 View {sec['section']} Details", use_container_width=True):
                                st.markdown(sec['details'])
                            st.write("")
            else:
                st.info("Agent 8 is currently inactive. Turn on the toggle switch above to run the analysis.")

else:
    st.info("Enter a stock ticker in the sidebar to begin analysis.")
