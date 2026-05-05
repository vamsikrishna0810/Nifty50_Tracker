import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from engine.backtester import run_price_action_strategy

st.set_page_config(page_title="Price Action Backtester", layout="wide")

st.sidebar.title("🔍 Market Explorer")

market_type = st.sidebar.selectbox("Market Category", ["Crypto", "Forex", "Stocks", "Indices"])

# Pre-loaded popular assets
tickers = {
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"],
    "Forex": ["EURUSD=X", "GBPUSD=X", "JPY=X"],
    "Stocks": ["NVDA", "TSLA", "AAPL", "MSFT", "RELIANCE.NS"],
    "Indices": ["^GSPC", "^IXIC", "^NSEI"]
}

symbol = st.sidebar.selectbox("Select Asset", tickers[market_type])
timeframe = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"])

st.sidebar.divider()
st.sidebar.subheader("Strategy Rules")
rr_min = st.sidebar.slider("Minimum Risk/Reward", 1.5, 5.0, 2.5)

if st.sidebar.button("Run Backtest"):
    with st.spinner(f"Fetching data and analyzing {symbol}..."):
        # Fetching data
        df = yf.download(symbol, period="60d", interval=timeframe)
        
        if not df.empty:
            # Flatten multi-index columns if yfinance returns them
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            results = run_price_action_strategy(df, rr_min)
            st.success("Analysis Complete!")
            
            # Layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"Trade Chart: {symbol} ({timeframe})")
                
                # Base Candlestick Chart
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="Price"
                )])
                
                # Overlay Supply and Demand Zones
                for z in results['zones']:
                    color = "rgba(0, 255, 0, 0.2)" if z['type'] == 'Demand' else "rgba(255, 0, 0, 0.2)"
                    fig.add_hrect(y0=z['bottom'], y1=z['top'], fillcolor=color, opacity=0.3, line_width=0)
                
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=600)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Dashboard Metrics")
                st.metric("Total Zones Found", len(results['zones']))
                st.metric("Risk/Reward Constraint", f"1 : {rr_min}")
                
                st.divider()
                st.write("Awaiting dashboard link to integrate exact trade log format and profit calculations.")
        else:
            st.error("No data found for this asset. Try a different timeframe.")
