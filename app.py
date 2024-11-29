import dash
from dash import dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import numpy as np

# Initialize Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Sample Data Fetch
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
        df["Vora Score"] = np.random.randint(50, 100, len(df))  # Example Score
        return df
    else:
        return pd.DataFrame()

df = fetch_data()

# Navbar
navbar = dbc.NavbarSimple(
    brand="CLP Dashboard",
    color="primary",
    dark=True,
)

# Layout
app.layout = dbc.Container([
    navbar,  # Add the Navbar at the top

    # Portfolio Section
    html.Div([
        html.H2("Portfolio Analysis", className="text-center my-4"),
        dbc.Row([
            dbc.Col(html.Div(id="portfolio-stats"), width=12),  # Portfolio Stats
        ], className="mb-4"),

        # Portfolio Table
        dbc.Card([
            dbc.CardHeader("Selected LPs"),
            dbc.CardBody(html.Div(id="portfolio-table"))
        ], className="mb-4"),
    ]),

    # Filters Section
    dbc.Card([
        dbc.CardHeader("Filters"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Chain"),
                    dcc.Dropdown(
                        id="chain-filter",
                        options=[{"label": chain, "value": chain} for chain in df["Chain"].unique()],
                        multi=True,
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Protocol"),
                    dcc.Dropdown(
                        id="protocol-filter",
                        options=[{"label": protocol, "value": protocol} for protocol in df["Protocol"].unique()],
                        multi=True,
                    )
                ], width=4),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Label("Min TVL (USD)"),
                    dcc.Input(id="tvl-filter", type="number", value=800000)
                ], width=4),
                dbc.Col([
                    html.Label("Min APY (%)"),
                    dcc.Input(id="apy-filter", type="number", value=5)
                ], width=4),
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
            style_table={"overflowX": "auto"},
            sort_action="native",
            filter_action="native",
        )),
    ]),
], fluid=True)

# Callbacks remain the same (e.g., for filtering, portfolio updates)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8080, debug=False)