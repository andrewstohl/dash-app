# live_dashboard.py

import streamlit as st
import requests
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

# --- Constants ---
API_URL = "https://yields.llama.fi/pools"
MAX_RETRIES = 3

CHAIN_OPTIONS = ["ALL"] + ["Arbitrum", "Avalanche", "Base", "BNB", "Ethereum", "Optimism", "Polygon", "Solana"]
PROJECT_OPTIONS = ["ALL"] + [
    "aave-v2", "aave-v3", "aerodrome-v1", "aerodrome-v2",
    "convex-finance", "orca", "pancakeswap-amm", "pancakeswap-amm-v3",
    "pendle", "quickswap-dex", "sushiswap", "uniswap-v2",
    "uniswap-v3", "velodrome-v2", "yearn-finance", "yldr"
]

DEFAULT_TVL_MIN = 800_000
DEFAULT_APY_MIN = 5.0
ADJUSTED_APY_RANGE = (1, 20)

# --- Fetch Data from API ---
@st.cache_data
def fetch_data():
    """Fetches data from the DeFi Llama Yield Pools API."""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            return response.json()["data"]
        except requests.exceptions.RequestException:
            retries += 1
    return []

# --- Normalize Metrics ---
def normalize(series):
    """Normalize a Pandas series using Min-Max scaling."""
    return (series - series.min()) / (series.max() - series.min())

# --- Calculate Vora LP Score ---
def calculate_vora_score(df):
    """Calculates the proprietary Vora LP Score for each liquidity pool."""
    df["NORMALIZED_TVL"] = normalize(df["TVL (USD)"])
    df["NORMALIZED_APY"] = normalize(df["APY (%)"])
    df["VORA_SCORE"] = (
        25 * df["NORMALIZED_TVL"] +
        20 * df["NORMALIZED_APY"] +
        15 * np.random.uniform(0, 1, len(df)) +  # Fee Efficiency (placeholder)
        10 * (1 - np.random.uniform(0, 1, len(df))) +  # Impermanent Loss (placeholder)
        30 * np.random.uniform(0, 1, len(df))  # Token Quality (placeholder)
    ).astype(int)  # Convert to integer
    return df

# --- Format Columns ---
def format_columns(df):
    """Format TVL and APY columns for proper display."""
    df["TVL (USD)"] = df["TVL (USD)"].apply(lambda x: f"${x:,.0f}")
    df["APY (%)"] = df["APY (%)"].apply(lambda x: f"{x:.2f}%")
    return df

# --- Main Dashboard ---
def main():
    st.title("Liquidity Pool Research Dashboard")
    st.write("Analyze, filter, and evaluate liquidity pools using real-time data from the DeFi Llama API.")

    # Fetch data
    st.write("Fetching data...")
    data = fetch_data()
    if not data:
        st.error("Failed to load data.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df = df.rename(columns={"chain": "CHAIN", "project": "PROJECT", "symbol": "SYMBOL", "tvlUsd": "TVL (USD)", "apy": "APY (%)"})
    df["TVL (USD)"] = df["TVL (USD)"].astype(float)
    df["APY (%)"] = df["APY (%)"].astype(float)

    # Initialize session state
    if "favorites" not in st.session_state:
        st.session_state["favorites"] = pd.DataFrame(columns=df.columns)
    if "selected" not in st.session_state:
        st.session_state["selected"] = pd.DataFrame(columns=df.columns)

    # Sync favorites and selected LPs
    df["FAVORITE"] = df["SYMBOL"].isin(st.session_state["favorites"]["SYMBOL"])
    df["SELECTED"] = df["SYMBOL"].isin(st.session_state["selected"]["SYMBOL"])

    # Calculate Vora LP Score
    df = calculate_vora_score(df)
    df = format_columns(df)

    # Sidebar Filters
    st.sidebar.header("Filters")
    selected_chains = st.sidebar.multiselect("Select Chains", CHAIN_OPTIONS, default="ALL")
    selected_projects = st.sidebar.multiselect("Select Projects", PROJECT_OPTIONS, default="ALL")
    tvl_min = st.sidebar.number_input("Minimum TVL (USD)", value=DEFAULT_TVL_MIN, step=50_000, format="%d")
    apy_min = st.sidebar.number_input("Minimum APY (%)", value=DEFAULT_APY_MIN, step=1.0, format="%.1f")
    adjusted_apy = st.sidebar.slider("Adjust APY Calculation (%)", min_value=ADJUSTED_APY_RANGE[0], max_value=ADJUSTED_APY_RANGE[1], value=1)

    # Apply Filters
    filtered_df = df.copy()
    if "ALL" not in selected_chains:
        filtered_df = filtered_df[filtered_df["CHAIN"].isin(selected_chains)]
    if "ALL" not in selected_projects:
        filtered_df = filtered_df[filtered_df["PROJECT"].isin(selected_projects)]
    filtered_df = filtered_df[filtered_df["TVL (USD)"].str.replace(",", "").str.replace("$", "").astype(float) >= tvl_min]
    filtered_df = filtered_df[filtered_df["APY (%)"].str.replace("%", "").astype(float) >= apy_min]

    # Interactive Table
    st.subheader("Filtered Liquidity Pools")
    grid_options = GridOptionsBuilder.from_dataframe(filtered_df)
    grid_options.configure_selection("multiple", use_checkbox=True, rowMultiSelectWithClick=True)
    grid_options.configure_column("FAVORITE", editable=True)
    grid_options = grid_options.build()

    grid_response = AgGrid(
        filtered_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True
    )

    # Update session state based on table
    updated_df = grid_response["data"]
    st.session_state["favorites"] = updated_df[updated_df["FAVORITE"]]
    st.session_state["selected"] = updated_df[updated_df["SELECTED"]]

    # Display Favorites Table
    st.subheader("Favorites")
    st.write(st.session_state["favorites"])

    # Display Selected LPs and Metrics
    st.subheader("Selected Liquidity Pools")
    selected_df = st.session_state["selected"]
    if not selected_df.empty:
        selected_df["TVL (USD)"] = selected_df["TVL (USD)"].str.replace(",", "").str.replace("$", "").astype(float)
        selected_df["APY (%)"] = selected_df["APY (%)"].str.replace("%", "").astype(float)
        avg_tvl = selected_df["TVL (USD)"].mean()
        avg_apy = selected_df["APY (%)"].mean()
        avg_vora_score = selected_df["VORA_SCORE"].mean()
        st.write(f"**Average TVL:** ${avg_tvl:,.0f}")
        st.write(f"**Average APY:** {avg_apy:.2f}%")
        st.write(f"**Average Vora Score:** {avg_vora_score:.0f}")
        st.write(selected_df)

    # Export Options
    st.download_button("Export Favorites", st.session_state["favorites"].to_csv(index=False), "favorites.csv")
    st.download_button("Export Selected", st.session_state["selected"].to_csv(index=False), "selected.csv")

if __name__ == "__main__":
    main()