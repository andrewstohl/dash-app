import streamlit as st
import pandas as pd
import requests

# Title for the dashboard
st.title("CLP Evaluation Dashboard")

# Fetch the live price of ETH from CoinGecko
st.write("### Live Market Data")
try:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(url).json()
    eth_price = response["ethereum"]["usd"]
    st.write(f"**Live ETH Price:** ${eth_price}")
except Exception as e:
    st.write("Error fetching live data. Please check your connection.")

# Example data for liquidity pools
st.write("### Liquidity Pool Data")
data = {
    "Pool": ["ETH/USDC", "BTC/ETH", "LINK/ETH", "MATIC/USDC"],
    "TVL ($)": [1000000, 800000, 600000, 500000],
    "Volume ($)": [500000, 300000, 200000, 150000],
    "APR (%)": [12, 10, 8, 7],
}
df = pd.DataFrame(data)

# Add a slider to filter pools by minimum TVL
min_tvl = st.slider("Filter Pools by Minimum TVL ($)", 0, 1500000, 500000)

# Filter the DataFrame based on the slider value
filtered_df = df[df["TVL ($)"] >= min_tvl]

# Organize layout into two columns
col1, col2 = st.columns(2)

# Display filtered table in the first column
with col1:
    st.write(f"### Filtered Pools (TVL >= ${min_tvl})")
    st.dataframe(filtered_df)

# Display bar chart in the second column
with col2:
    st.write("### TVL Distribution")
    st.bar_chart(filtered_df.set_index("Pool")["TVL ($)"])