import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# --- Streamlit Page Config ---
st.set_page_config(page_title="Crypto Portfolio Tracker", layout="wide")

# --- Settings ---
refresh_interval = 60  # seconds
days_to_track = 7
tickers = ["BTC-USD", "ETH-USD"]
ema_period = 7  # Exponential Moving Average period (7-day)

# --- Auto Refresh Logic ---
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = datetime.now()

elapsed = (datetime.now() - st.session_state["last_refresh"]).seconds
remaining = refresh_interval - elapsed

st.markdown(f"⏳ **Next update in:** {max(remaining,0)} seconds", unsafe_allow_html=True)

if elapsed >= refresh_interval:
    st.session_state["last_refresh"] = datetime.now()
    st.rerun()

# --- Fetch Data ---
end = datetime.now()
start = end - pd.Timedelta(days=days_to_track)

raw_data = yf.download(tickers, start=start, end=end)
if "Adj Close" in raw_data.columns:
    data = raw_data["Adj Close"]
else:
    data = raw_data["Close"]
data = data.dropna()

# --- Compute Portfolios ---
btc_only = data["BTC-USD"] / data["BTC-USD"].iloc[0]
eth_only = data["ETH-USD"] / data["ETH-USD"].iloc[0]
mixed = 0.5 * btc_only + 0.5 * eth_only  # 50/50 portfolio (average)

# --- Portfolio Chart ---
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=btc_only.index, y=btc_only, name="100% BTC", line=dict(width=3)))
fig1.add_trace(go.Scatter(x=eth_only.index, y=eth_only, name="100% ETH", line=dict(width=3)))
fig1.add_trace(go.Scatter(
    x=mixed.index, y=mixed,
    name="50% BTC + 50% ETH (Average)", line=dict(width=4, dash="dash", color="black")
))

fig1.update_layout(
    title=f"Portfolio Performance (Last {days_to_track} Days)",
    xaxis_title="Date",
    yaxis_title="Normalized Value (Base = 1.0)",
    template="plotly_white",
    hovermode="x unified",
    height=800,
    font=dict(size=16)
)

st.plotly_chart(fig1, use_container_width=True)
st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- BTC Price + 7-Day EMA ---
btc_price = data["BTC-USD"]
btc_ema = btc_price.ewm(span=ema_period, adjust=False).mean()

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=btc_price.index,
    y=btc_price,
    name="BTC-USD Price",
    line=dict(width=3, color="orange")
))
fig2.add_trace(go.Scatter(
    x=btc_ema.index,
    y=btc_ema,
    name=f"{ema_period}-Day EMA",
    line=dict(width=3, color="black", dash="dot")
))

fig2.update_layout(
    title=f"Bitcoin (BTC-USD) Price & {ema_period}-Day EMA",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_white",
    hovermode="x unified",
    height=800,
    font=dict(size=16)
)

st.plotly_chart(fig2, use_container_width=True)
st.caption(f"📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- Latest Portfolio Values ---
latest_values = pd.DataFrame({
    "Portfolio": ["100% BTC", "100% ETH", "50% BTC + 50% ETH (Average)"],
    "Value": [btc_only.iloc[-1], eth_only.iloc[-1], mixed.iloc[-1]]
})

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.markdown("### 📊 Latest Portfolio Values")
st.write(f"**Last updated:** {update_time}")
st.table(latest_values.style.format({"Value": "{:.4f}"}))

# --- Market Insight / Interpretation ---
st.markdown("### 🧠 Portfolio Performance Insight")

btc_return = btc_only.iloc[-1] - 1
eth_return = eth_only.iloc[-1] - 1
mix_return = mixed.iloc[-1] - 1

if eth_return > btc_return and eth_return > mix_return:
    st.success("**Ethereum (ETH)** is currently outperforming both BTC and the mixed portfolio — risk-on sentiment likely active.")
elif btc_return > eth_return:
    st.warning("**Bitcoin (BTC)** is outperforming Ethereum — market may be favoring safety or early in a BTC-led cycle.")
else:
    st.info("The 50/50 portfolio is holding its ground well — balanced performance across BTC and ETH.")
