import dash
from dash import dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import numpy as np

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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

# Load data
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

# Sort data by Vora Score descending by default
df = df.sort_values(by="Vora Score", ascending=False)

# App layout
app.layout = dbc.Container([
    # Portfolio Stats and Selected LPs Table
    html.Div([
        html.H2("Portfolio Stats", style={"text-align": "center"}),

        # Aggregate Metrics
        html.Div(id="portfolio-stats", style={"margin-bottom": "20px"}),

        # Portfolio Table
        html.Div(id="portfolio-table", style={"margin-bottom": "40px"})
    ], style={"margin-bottom": "40px"}),

    # Hidden store for portfolio data
    dcc.Store(id="portfolio-store", data=[]),

    # Filters Section
    dbc.Row([
        dbc.Col([
            html.Label("Chain"),
            dcc.Dropdown(
                id="chain-filter",
                options=[{"label": chain, "value": chain} for chain in valid_chains],
                value=[],  # Default: No chain selected
                multi=True
            )
        ], width=2),
        dbc.Col([
            html.Label("Protocol"),
            dcc.Dropdown(
                id="protocol-filter",
                options=[{"label": protocol, "value": protocol} for protocol in valid_protocols],
                value=[],  # Default: No protocol selected
                multi=True
            )
        ], width=2),
        dbc.Col([
            html.Label("Token 1"),
            dcc.Input(id="token1-filter", type="text", placeholder="Token 1")
        ], width=2),
        dbc.Col([
            html.Label("Token 2"),
            dcc.Input(id="token2-filter", type="text", placeholder="Token 2")
        ], width=2),
        dbc.Col([
            html.Label("Min TVL (USD)"),
            dcc.Input(id="tvl-filter", type="number", value=800000)  # Default: 800,000
        ], width=2),
        dbc.Col([
            html.Label("Min APY (%)"),
            dcc.Input(id="apy-filter", type="number", value=5)  # Default: 5
        ], width=2),
    ], style={"margin-bottom": "20px"}),

    # Results Table
    html.Div([
        html.H4("Filtered Liquidity Pools"),
        dash_table.DataTable(
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
            sort_action="native",
            filter_action="native",
        )
    ])
], fluid=True)

# Callbacks
@app.callback(
    [Output("lp-table", "data"),
     Output("lp-table", "selected_rows")],
    [
        Input("chain-filter", "value"),
        Input("protocol-filter", "value"),
        Input("token1-filter", "value"),
        Input("token2-filter", "value"),
        Input("tvl-filter", "value"),
        Input("apy-filter", "value"),
        State("portfolio-store", "data")
    ]
)
def update_results(chain_filter, protocol_filter, token1_filter, token2_filter, tvl_filter, apy_filter, portfolio_data):
    # Start with the full DataFrame
    filtered_df = df.copy()

    # Apply chain filter
    if chain_filter:
        filtered_df = filtered_df[filtered_df["Chain"].isin(chain_filter)]

    # Apply protocol filter
    if protocol_filter:
        filtered_df = filtered_df[filtered_df["Protocol"].isin(protocol_filter)]

    # Apply token1 filter (partial match in Symbol column)
    if token1_filter:
        filtered_df = filtered_df[filtered_df["Symbol"].str.contains(token1_filter, case=False, na=False)]

    # Apply token2 filter (partial match in Symbol column)
    if token2_filter:
        filtered_df = filtered_df[filtered_df["Symbol"].str.contains(token2_filter, case=False, na=False)]

    # Apply TVL filter
    if tvl_filter:
        filtered_df = filtered_df[filtered_df["TVL (USD)"] >= tvl_filter]

    # Apply APY filter
    if apy_filter:
        filtered_df = filtered_df[filtered_df["APY (%)"] >= apy_filter]

    # Find rows that should remain selected (IDs matching portfolio data)
    selected_rows = [
        i for i, row in filtered_df.iterrows()
        if row.to_dict() in portfolio_data
    ]

    # Sort by Vora Score descending
    filtered_df = filtered_df.sort_values(by="Vora Score", ascending=False)

    return filtered_df.to_dict("records"), selected_rows


@app.callback(
    [Output("portfolio-store", "data"),
     Output("portfolio-stats", "children"),
     Output("portfolio-table", "children")],
    [Input("lp-table", "derived_virtual_data"),
     Input("lp-table", "derived_virtual_selected_rows")],
    [State("portfolio-store", "data")]
)
def update_portfolio(data, selected_rows, portfolio_data):
    if not data:
        return portfolio_data, html.P("No LPs selected."), html.P("No LPs selected.")

    # Get selected LPs
    selected_df = pd.DataFrame(data).iloc[selected_rows]

    # Update portfolio: add selected LPs and remove deselected ones
    portfolio_df = pd.DataFrame(portfolio_data)
    portfolio_df = pd.concat([portfolio_df, selected_df]).drop_duplicates()

    # Aggregate stats
    avg_tvl = portfolio_df["TVL (USD)"].mean()
    avg_apy = portfolio_df["APY (%)"].mean()
    avg_vora = portfolio_df["Vora Score"].mean()

    portfolio_stats = html.Div([
        html.H4("Portfolio Metrics"),
        html.P(f"Average TVL: ${avg_tvl:,.0f}"),
        html.P(f"Average APY: {avg_apy:.2f}%"),
        html.P(f"Average Vora Score: {avg_vora:.0f}")
    ])

    portfolio_table = dash_table.DataTable(
        columns=[
            {"name": "Symbol", "id": "Symbol"},
            {"name": "Chain", "id": "Chain"},
            {"name": "Protocol", "id": "Protocol"},
            {"name": "TVL (USD)", "id": "TVL (USD)"},
            {"name": "APY (%)", "id": "APY (%)"},
            {"name": "Vora Score", "id": "Vora Score"}
        ],
        data=portfolio_df.to_dict("records"),
        style_table={"overflowX": "auto"}
    )

    return portfolio_df.to_dict("records"), portfolio_stats, portfolio_table


# Run app
if __name__ == "__main__":
    app.run_server(debug=False)