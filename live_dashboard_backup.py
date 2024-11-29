import requests
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from sklearn.preprocessing import MinMaxScaler

# Fetch LP data from DeFi Llama API
@st.cache_data
def fetch_lp_data():
    try:
        url = "https://yields.llama.fi/pools"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["data"]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on failure

# Sidebar for filters
st.sidebar.header("Filters")

# Define allowed projects
allowed_projects = [
    "aave-v2", "aave-v3", "aerodrome-v1", "aerodrome-v2", "convex-finance", "ethena",
    "orca", "pancakeswap-amm", "pancakeswap-amm-v3", "pendle", "quickswap-dex",
    "sushiswap", "uniswap-v2", "uniswap-v3", "velodrome-v2", "yearn-finance", "yldr"
]

# Define allowed networks
allowed_networks = [
    "arbitrum", "avalanche", "base", "bnb", "ethereum",
    "optimism", "polygon", "solana"
]

# Pool types
pool_types = ["All", "Stable", "Volatile", "Concentrated"]

# Fetch data
lp_data = fetch_lp_data()

if not lp_data.empty:
    # Pool type filter
    selected_pool_type = st.sidebar.selectbox("Select Pool Type", pool_types, index=0)

    # Filter by project(s)
    projects = sorted(lp_data["project"].dropna().unique())
    selected_projects = st.sidebar.multiselect(
        "Select Project(s)", ["All"] + projects, default="All"
    )

    # Filter by network(s)
    filtered_networks = lp_data[lp_data["chain"].str.lower().isin(allowed_networks)]
    networks = sorted(filtered_networks["chain"].dropna().unique())
    selected_networks = st.sidebar.multiselect(
        "Select Network(s)", ["All"] + networks, default="All"
    )

    # Minimum TVL filter
    min_tvl = st.sidebar.text_input("Minimum TVL ($)", value="0")

    # Minimum APY filter
    min_apy = st.sidebar.text_input("Minimum APY (%)", value="0")

    # Coin search filters
    coin_1 = st.sidebar.text_input("Search for Coin 1 (e.g., USDC)")
    coin_2 = st.sidebar.text_input("Search for Coin 2 (optional, e.g., WETH)")

    # Apply filters
    if "All" not in selected_projects:
        lp_data = lp_data[lp_data["project"].isin(selected_projects)]

    if "All" not in selected_networks:
        lp_data = lp_data[lp_data["chain"].isin(selected_networks)]

    if min_tvl.isdigit():
        lp_data = lp_data[lp_data["tvlUsd"] >= int(min_tvl)]

    if min_apy.replace(".", "", 1).isdigit():
        lp_data = lp_data[lp_data["apy"].fillna(0) >= float(min_apy)]

    if coin_1:
        lp_data = lp_data[lp_data["symbol"].str.contains(coin_1.upper(), na=False)]

    if coin_2:
        lp_data = lp_data[lp_data["symbol"].str.contains(coin_2.upper(), na=False)]

    # Keep raw values for display
    lp_data["Raw TVL"] = lp_data["tvlUsd"]
    lp_data["Raw APY"] = lp_data["apy"]

    # Convert ilRisk to numeric
    lp_data["ilRisk"] = pd.to_numeric(lp_data["ilRisk"], errors="coerce").fillna(0)

    # Normalize metrics for scoring
    scaler = MinMaxScaler()
    lp_data[["tvlUsd", "apy", "volumeUsd1d", "ilRisk"]] = scaler.fit_transform(
        lp_data[["tvlUsd", "apy", "volumeUsd1d", "ilRisk"]]
    )

    # Define weights for scoring
    weights = {
        "tvlUsd": 0.3,       # 30% weight to TVL
        "apy": 0.4,          # 40% weight to APY
        "volumeUsd1d": 0.2,  # 20% weight to Volume
        "ilRisk": 0.1        # 10% weight to Risk (negative influence)
    }

    # Calculate Vora Fund Score
    lp_data["Vora Score"] = (
        weights["tvlUsd"] * lp_data["tvlUsd"] +
        weights["apy"] * lp_data["apy"] +
        weights["volumeUsd1d"] * lp_data["volumeUsd1d"] -
        weights["ilRisk"] * lp_data["ilRisk"]
    )

    # Sort by Vora Score
    lp_data = lp_data.sort_values(by="Vora Score", ascending=False)

    # Display top LPs with scores
    display_data = lp_data[["symbol", "project", "chain", "Raw TVL", "Raw APY", "volumeUsd1d", "Vora Score"]].copy()
    display_data.rename(columns={
        "symbol": "Pool Pair",
        "project": "Protocol",
        "chain": "Network",
        "Raw TVL": "TVL",
        "Raw APY": "APY (%)",
        "volumeUsd1d": "Daily Volume ($)",
        "Vora Score": "Score"
    }, inplace=True)

    # Configure Ag-Grid options
    gb = GridOptionsBuilder.from_dataframe(display_data)
    gb.configure_column("TVL", type=["numericColumn"], valueFormatter="x.toLocaleString('en-US', {style: 'currency', currency: 'USD'})")
    gb.configure_column("APY (%)", type=["numericColumn"], valueFormatter="(x === null || x === undefined) ? '' : x.toFixed(2) + '%'")
    gb.configure_column("Daily Volume ($)", type=["numericColumn"], valueFormatter="x.toLocaleString('en-US', {style: 'currency', currency: 'USD'})")
    gb.configure_column("Score", type=["numericColumn"], valueFormatter="x.toFixed(2)")
    gb.configure_default_column(sortable=True)

    grid_options = gb.build()

    # Display table using Ag-Grid
    st.write("### Top Liquidity Pools by Vora Fund Score")
    AgGrid(display_data, gridOptions=grid_options, use_container_width=True)
else:
    st.write("No data available. Please try again later.")