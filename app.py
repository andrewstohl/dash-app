import dash
from dash import dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import numpy as np

# Initialize Dash app with a dark theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Fetch real-time data from DeFi Llama API
def fetch_data():
    url = "https://yields.llama.fi/pools"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["data"])
        df = df[["symbol", "chain", "project", "tvlUsd", "apy"]]
        df.rename(columns={
            "symbol": "Symbol",
            "chain": "Chain",
            "project": "Protocol",
            "tvlUsd": "TVL (USD)",
            "apy": "APY (%)"
        }, inplace=True)
        df["Vora Score"] = np.random.randint(50, 100, len(df))  # Placeholder for Vora Score
        return df
    else:
        return pd.DataFrame()

# Load and preprocess data
df = fetch_data()

# Limit chains and protocols to specified options
valid_chains = ["Arbitrum", "Avalanche", "Base", "BNB", "Ethereum", "Optimism", "Polygon", "Solana"]
valid_protocols = [
    "aave-v2", "aave-v3", "aerodrome-v1", "aerodrome-v2", "convex-finance", "orca",
    "pancakeswap-amm", "pancakeswap-amm-v3", "pendle", "quickswap-dex", "sushiswap",
    "uniswap-v2", "uniswap-v3", "velodrome-v2", "yearn-finance", "yldr"
]
df = df[df["Chain"].isin(valid_chains)]
df = df[df["Protocol"].isin(valid_protocols)]
df = df.sort_values(by="Vora Score", ascending=False)

# Navbar
navbar = dbc.NavbarSimple(
    brand="CLP Dashboard",
    brand_style={"font-size": "1.5em", "font-weight": "bold"},
    color="dark",
    dark=True,
)

# App layout
app.layout = dbc.Container([
    navbar,  # Navbar at the top

    # Portfolio Analysis Section at the Top
    dbc.Card([
        dbc.CardHeader("Portfolio Analysis"),
        dbc.CardBody([
            html.Div(id="portfolio-stats", className="mb-3"),
            html.Div(id="portfolio-table")
        ]),
    ], className="mb-4"),

    # Filters Section
    dbc.Card([
        dbc.CardHeader("Filters"),
        dbc.CardBody([
            dbc.Row([
                # Chain Filter
                dbc.Col([
                    html.Label("Chain", style={"font-size": "1em"}),
                    dcc.Dropdown(
                        id="chain-filter",
                        options=[{"label": chain, "value": chain} for chain in valid_chains],
                        multi=True,
                        style={"color": "black"}
                    )
                ], width=2),

                # Protocol Filter
                dbc.Col([
                    html.Label("Protocol", style={"font-size": "1em"}),
                    dcc.Dropdown(
                        id="protocol-filter",
                        options=[{"label": protocol, "value": protocol} for protocol in valid_protocols],
                        multi=True,
                        style={"color": "black"}
                    )
                ], width=2),

                # Token 1 Filter
                dbc.Col([
                    html.Label("Token 1", style={"font-size": "1em"}),
                    dcc.Input(
                        id="token1-filter",
                        type="text",
                        placeholder="Search Token 1",
                        style={"color": "black"}
                    )
                ], width=2),

                # Token 2 Filter
                dbc.Col([
                    html.Label("Token 2", style={"font-size": "1em"}),
                    dcc.Input(
                        id="token2-filter",
                        type="text",
                        placeholder="Search Token 2",
                        style={"color": "black"}
                    )
                ], width=2),

                # Min TVL Filter
                dbc.Col([
                    html.Label("Min TVL", style={"font-size": "1em"}),
                    dcc.Input(
                        id="tvl-filter",
                        type="number",
                        value=800000,
                        style={"color": "black"}
                    )
                ], width=2),

                # Min APY Filter
                dbc.Col([
                    html.Label("Min APY", style={"font-size": "1em"}),
                    dcc.Input(
                        id="apy-filter",
                        type="number",
                        value=5,
                        style={"color": "black"}
                    )
                ], width=2),
            ], className="mt-3"),
        ]),
    ], className="mb-4"),

    # Results Table
    dbc.Card([
        dbc.CardHeader("Filtered Liquidity Pools"),
        dbc.CardBody(dash_table.DataTable(
            id="lp-table",
            columns=[
                {"name": "Symbol", "id": "Symbol"},
                {"name": "Chain", "id": "Chain"},
                {"name": "Protocol", "id": "Protocol"},
                {"name": "TVL (USD)", "id": "TVL (USD)", "type": "numeric", "format": {"specifier": "$,.0f"}},
                {"name": "APY (%)", "id": "APY (%)", "type": "numeric", "format": {"specifier": ".2f"}},
                {"name": "Vora Score", "id": "Vora Score", "type": "numeric"},
            ],
            data=df.to_dict("records"),
            row_selectable="multi",  # Enable row selection
            selected_rows=[],  # Keep track of selected rows
            style_table={"overflowX": "auto"},
            style_header={"backgroundColor": "black", "color": "white", "fontWeight": "bold"},
            style_cell={"backgroundColor": "#222", "color": "white"},
            sort_action="native",
            filter_action="native",
        )),
    ], className="mb-4"),
], fluid=True)

# Callbacks for filtering and portfolio selection
@app.callback(
    Output("lp-table", "data"),
    [
        Input("chain-filter", "value"),
        Input("protocol-filter", "value"),
        Input("token1-filter", "value"),
        Input("token2-filter", "value"),
        Input("tvl-filter", "value"),
        Input("apy-filter", "value"),
    ]
)
def update_results(chain_filter, protocol_filter, token1_filter, token2_filter, tvl_filter, apy_filter):
    filtered_df = df.copy()

    if chain_filter:
        filtered_df = filtered_df[filtered_df["Chain"].isin(chain_filter)]
    if protocol_filter:
        filtered_df = filtered_df[filtered_df["Protocol"].isin(protocol_filter)]
    if token1_filter:
        filtered_df = filtered_df[filtered_df["Symbol"].str.contains(token1_filter, case=False, na=False)]
    if token2_filter:
        filtered_df = filtered_df[filtered_df["Symbol"].str.contains(token2_filter, case=False, na=False)]
    if tvl_filter:
        filtered_df = filtered_df[filtered_df["TVL (USD)"] >= tvl_filter]
    if apy_filter:
        filtered_df = filtered_df[filtered_df["APY (%)"] >= apy_filter]

    return filtered_df.to_dict("records")


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8080, debug=False)