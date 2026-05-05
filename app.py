import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from engine.backtester import run_price_action_strategy

st.set_page_config(page_title="Price Action Backtester V2", layout="wide")

st.sidebar.title("🔍 Market Explorer")

market_type = st.sidebar.selectbox("Market Category", ["Crypto", "Forex", "Stocks", "Indices"])

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
        df = yf.download(symbol, period="60d", interval=timeframe)
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            results = run_price_action_strategy(df, rr_min)
            trades_df = pd.DataFrame(results['trades'])
            
            st.success("Analysis Complete!")
            
            # --- METRICS ROW ---
            st.subheader("Performance Dashboard")
            m1, m2, m3, m4 = st.columns(4)
            
            total_trades = len(trades_df)
            wins = len(trades_df[trades_df['outcome'] == 'Win']) if total_trades > 0 else 0
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            total_r = trades_df['pnl'].sum() if total_trades > 0 else 0
            
            m1.metric("Total Trades Taken", total_trades)
            m2.metric("Win Rate", f"{win_rate:.1f}%")
            m3.metric("Net Profit (Risk Units)", f"{total_r:.2f} R", delta=f"{total_r:.2f}")
            m4.metric("Risk/Reward Profile", f"1 : {rr_min}")
            
            st.divider()
            
            # --- CHART & LOGS ROW ---
            col1, col2 = st.columns([2.5, 1.5])
            
            with col1:
                st.subheader(f"Trade Execution Chart: {symbol}")
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"
                )])
                
                # Draw Zones
                for z in results['zones']:
                    color = "rgba(0, 255, 0, 0.15)" if z['type'] == 'Demand' else "rgba(255, 0, 0, 0.15)"
                    fig.add_hrect(y0=z['bottom'], y1=z['top'], fillcolor=color, opacity=0.3, line_width=0)
                
                # Plot Entries
                if total_trades > 0:
                    entries_long = trades_df[trades_df['type'] == 'Long']
                    entries_short = trades_df[trades_df['type'] == 'Short']
                    
                    fig.add_trace(go.Scatter(x=entries_long['entry_time'], y=entries_long['entry'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'), name='Long Entry'))
                    fig.add_trace(go.Scatter(x=entries_short['entry_time'], y=entries_short['entry'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='Short Entry'))
                
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=600, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Trade Log")
                if total_trades > 0:
                    # Format dataframe for display
                    display_df = trades_df[['entry_time', 'type', 'outcome', 'pnl']].copy()
                    display_df['entry_time'] = display_df['entry_time'].dt.strftime('%b %d, %H:%M')
                    
                    def color_outcome(val):
                        color = '#00ff00' if val == 'Win' else '#ff0000' if val == 'Loss' else 'gray'
                        return f'color: {color}'
                        
                    st.dataframe(display_df.style.map(color_outcome, subset=['outcome']), height=600, use_container_width=True)
                else:
                    st.info("No trades met the criteria in this period.")
        else:
            st.error("No data found for this asset. Try a different timeframe.")
