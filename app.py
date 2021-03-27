import dash
import numpy as np
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from ETHQuantoFutures.TradingUtil import TradeSetup


trade_setup = TradeSetup()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash("Shorting Ethereum quanto futures contracts on BitMEX", external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Quanto"

row_starting_prices = html.Div([
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                id="loading-query",
                fullscreen=True,
                children=html.H5(id="starting-prices", children=trade_setup.starting_parameters.html_summary)
            )], width={"order": "first"}),
        dbc.Col([
            html.Button('Query exchanges', id="query-btn")
        ])
    ], align="center")
])

row_bitcon_amount = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Input(id="amount-btc-inp",
                      type="number",
                      value=0,
                      style={'width': '150px'}),
        ], width={"order": "first"}),
        dbc.Col([
            html.P(id="amount-btc-txt",
                   children=f"[BTC] : Bitcoin holded on BitMEX (fully hedged to synthetic USD) · {trade_setup.bitmex_starting_value} USD as investment")
        ])
    ], align="center")
])

row_eth_spot_amount = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Input(id="amount-eth-spot-inp",
                      type="number",
                      value=0,
                      style={'width': '150px'}),
        ], width={"order": "first"}),
        dbc.Col([
            html.P(id="amount-eth-spot-txt",
                   children=f"[ETH] : Ethereum holded as spot · {trade_setup.eth_spot_value} USD as investment")
        ])
    ], align="center")
])

row_eth_quanto_amount = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Input(id="amount-eth-contracts-inp",
                      type="number",
                      value=0,
                      style={'width': '150px'}),
        ], width={"order": "first"}),
        dbc.Col([
            html.P(id="amount-eth-contracts-txt",
                   children=f"[contracts] : Ethereum quanto futures contracts shorted on BitMEX"
                            f" · {trade_setup.eth_quanto_futures_btc_value} BTC in value"
                            f" · {trade_setup.eth_quanto_futures_value} USD in value")
        ])
    ], align="center")
])

row_btc_calls = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Input(id="amount-btc-calls-inp",
                      type="number",
                      value=0,
                      style={'width': '150px'}),
        ], width={"order": "first"}),
        dbc.Col([
            dcc.Dropdown(
                id="strike-btc-calls",
                options=[]
            )
        ]),
        dbc.Col([
            html.P(id="btc-calls-txt",
                   children=f"[BTC] : Bitcoin call options to buy on Deribit with the specified strike price. "
                            f"Cost is {trade_setup.portfolio.cost_of_btc_calls}")
        ])
    ])
])

row_eth_calls = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Input(id="amount-eth-calls-inp",
                      type="number",
                      value=0,
                      style={'width': '150px'}),
        ], width={"order": "first"}),
        dbc.Col([
            dcc.Dropdown(
                id="strike-eth-calls",
                options=[]
            )
        ]),
        dbc.Col([
            html.P(id="eth-calls-txt",
                   children=f"[ETH] : Ethereum call options to buy on Deribit with the specified strike price. "
                            f"Cost is {trade_setup.portfolio.cost_of_eth_calls}")
        ])
    ])
])

row_btc_puts = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Input(id="amount-btc-puts-inp",
                      type="number",
                      value=0,
                      style={'width': '150px'}),
        ], width={"order": "first"}),
        dbc.Col([
            dcc.Dropdown(
                id="strike-btc-puts",
                options=[]
            )
        ]),
        dbc.Col([
            html.P(id="btc-puts-txt",
                   children=f"[BTC] : Bitcoin put options to buy on Deribit with the specified strike price. "
                            f"Cost is {trade_setup.portfolio.cost_of_btc_puts}")
        ])
    ])
])

row_eth_puts = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Input(id="amount-eth-puts-inp",
                      type="number",
                      value=0,
                      style={'width': '150px'}),
        ], width={"order": "first"}),
        dbc.Col([
            dcc.Dropdown(
                id="strike-eth-puts",
                options=[]
            )
        ]),
        dbc.Col([
            html.P(id="eth-puts-txt",
                   children=f"[ETH] : Ethereum put options to buy on Deribit with the specified strike price. "
                            f"Cost is {trade_setup.portfolio.cost_of_eth_puts}")
        ])
    ])
])

app.layout = dbc.Container(children=[
    row_starting_prices,
    html.Br(),
    row_bitcon_amount,
    html.Br(),
    row_eth_quanto_amount,
    html.Br(),
    row_eth_spot_amount,
    html.Br(),
    row_btc_calls,
    html.Br(),
    row_eth_calls,
    html.Br(),
    row_btc_puts,
    html.Br(),
    row_eth_puts,
    html.Br(),
    html.P("Premium left when closing positions, expressed in percentage"),
    dcc.Slider(
        id='prem-left-close-slider',
        min=0,
        max=100,
        step=0.1,
        value=0,
        tooltip=dict(always_visible=False)
    ),
    dcc.Loading(
        id="loading-figure",
        children=dcc.Graph(id="graph")
    )
])

# QUERY BUTTON -> STARTING PRICES TEXT
@app.callback(
    dash.dependencies.Output('starting-prices', 'children'),    # this is a loading component
    [dash.dependencies.Input('query-btn', 'n_clicks')])
def update_starting_prices_text(_):
    trade_setup.starting_parameters.query()
    return trade_setup.starting_parameters.html_summary


# QUERY BUTTON -> STARTING PRICES TEXT -> BTC CALLS DROPDOWN
@app.callback(
    dash.dependencies.Output('strike-btc-calls', 'options'),
    [dash.dependencies.Input('starting-prices', 'children')])
def set_possible_btc_calls(_):
    prices = [call['strike'] for call in trade_setup.starting_parameters.btc_call_options]
    prices.sort()
    return [{'label': pr, 'value': pr} for pr in prices]


# QUERY BUTTON -> STARTING PRICES TEXT -> ETH CALLS DROPDOWN
@app.callback(
    dash.dependencies.Output('strike-eth-calls', 'options'),
    [dash.dependencies.Input('starting-prices', 'children')])
def set_possible_eth_calls(_):
    prices = [call['strike'] for call in trade_setup.starting_parameters.eth_call_options]
    prices.sort()
    return [{'label': pr, 'value': pr} for pr in prices]


# QUERY BUTTON -> STARTING PRICES TEXT -> BTC PUTS DROPDOWN
@app.callback(
    dash.dependencies.Output('strike-btc-puts', 'options'),
    [dash.dependencies.Input('starting-prices', 'children')])
def set_possible_btc_puts(_):
    prices = [call['strike'] for call in trade_setup.starting_parameters.btc_put_options]
    prices.sort()
    return [{'label': pr, 'value': pr} for pr in prices]


# QUERY BUTTON -> STARTING PRICES TEXT -> ETH PUTS DROPDOWN
@app.callback(
    dash.dependencies.Output('strike-eth-puts', 'options'),
    [dash.dependencies.Input('starting-prices', 'children')])
def set_possible_eth_puts(_):
    prices = [call['strike'] for call in trade_setup.starting_parameters.eth_put_options]
    prices.sort()
    return [{'label': pr, 'value': pr} for pr in prices]


# ANY TEXT FIELD -> GRAPH
@app.callback(
    dash.dependencies.Output('graph', 'figure'),                # this is a loading component
    [dash.dependencies.Input('starting-prices', 'children'),
     dash.dependencies.Input('amount-btc-txt', 'children'),
     dash.dependencies.Input('amount-eth-spot-txt', 'children'),
     dash.dependencies.Input('amount-eth-contracts-txt', 'children'),
     dash.dependencies.Input('btc-calls-txt', 'children'),
     dash.dependencies.Input('eth-calls-txt', 'children'),
     dash.dependencies.Input('btc-puts-txt', 'children'),
     dash.dependencies.Input('eth-puts-txt', 'children'),
     dash.dependencies.Input('prem-left-close-slider', 'value')])
def update_graph_on_any_param_change(txt0, txt1, txt2, txt3, txt4, txt5, txt6, txt7, prem_left):
    trade_setup.set_exit_premium(prem_left / 100)
    return build_plot()


# BTC AMOUNT INPUT -> BTC AMOUNT TEXT
@app.callback(
    dash.dependencies.Output('amount-btc-txt', 'children'),
    dash.dependencies.Input('amount-btc-inp', 'value'))
def update_amount_btc(amount_btc):
    trade_setup.portfolio.set_btc_amount_bitmex(amount_btc)
    return f"[BTC] : Bitcoin held on BitMEX (fully hedged to synthetic USD) · {trade_setup.bitmex_starting_value} USD as investment"


# ETH AMOUNT INPUT -> ETH AMOUNT TEXT
@app.callback(
    dash.dependencies.Output('amount-eth-spot-txt', 'children'),
    dash.dependencies.Input('amount-eth-spot-inp', 'value'))
def update_amount_eth_spot(amount_eth_spot):
    trade_setup.portfolio.set_eth_spot_amount(amount_eth_spot)
    return f"[ETH] : Ethereum held as spot · {trade_setup.eth_spot_value} USD as investment"


# ETH CONTRACTS INPUT -> ETH CONTRACTS TEXT
@app.callback(
    dash.dependencies.Output('amount-eth-contracts-txt', 'children'),
    dash.dependencies.Input('amount-eth-contracts-inp', 'value'))
def update_amount_eth_contracts(amount_eth_contracts):
    trade_setup.portfolio.set_eth_contracts_to_short(amount_eth_contracts)
    return f"[contracts] : Ethereum quanto futures contracts shorted on BitMEX" \
           f" · {trade_setup.eth_quanto_futures_btc_value} BTC in value" \
           f" · {trade_setup.eth_quanto_futures_value} USD in value"


# ETH CALLS INPUT -> ETH CALLS TEXT
@app.callback(
    dash.dependencies.Output('eth-calls-txt', 'children'),
    [dash.dependencies.Input('amount-eth-calls-inp', 'value'),
     dash.dependencies.Input('strike-eth-calls', 'value')])
def update_amount_eth_calls(amount_eth_calls, strike_eth_calls):
    trade_setup.portfolio.eth_calls_amount = amount_eth_calls
    for call in trade_setup.starting_parameters.eth_call_options:
        if call['strike'] == strike_eth_calls:
            trade_setup.portfolio.eth_calls_premium = call['underlying_price'] * call['best_ask_price']
            trade_setup.portfolio.eth_calls_strike = call['strike']
            break
    return f"[ETH] : Ethereum call options to buy on Deribit with the specified strike price. "\
           f"Cost is {trade_setup.portfolio.cost_of_eth_calls}"


# BTC CALLS INPUT -> BTC CALLS TEXT
@app.callback(
    dash.dependencies.Output('btc-calls-txt', 'children'),
    [dash.dependencies.Input('amount-btc-calls-inp', 'value'),
     dash.dependencies.Input('strike-btc-calls', 'value')])
def update_amount_btc_calls(amount_btc_calls, strike_btc_calls):
    trade_setup.portfolio.btc_calls_amount = amount_btc_calls
    for call in trade_setup.starting_parameters.btc_call_options:
        if call['strike'] == strike_btc_calls:
            trade_setup.portfolio.btc_calls_premium = call['underlying_price'] * call['best_ask_price']
            trade_setup.portfolio.btc_calls_strike = call['strike']
            break
    return f"[BTC] : Bitcoin call options to buy on Deribit with the specified strike price. "\
           f"Cost is {trade_setup.portfolio.cost_of_btc_calls}"


# ETH PUTS INPUT -> ETH PUTS TEXT
@app.callback(
    dash.dependencies.Output('eth-puts-txt', 'children'),
    [dash.dependencies.Input('amount-eth-puts-inp', 'value'),
     dash.dependencies.Input('strike-eth-puts', 'value')])
def update_amount_eth_puts(amount_eth_puts, strike_eth_puts):
    trade_setup.portfolio.eth_puts_amount = amount_eth_puts
    for put in trade_setup.starting_parameters.eth_put_options:
        if put['strike'] == strike_eth_puts:
            trade_setup.portfolio.eth_puts_premium = put['underlying_price'] * put['best_ask_price']
            trade_setup.portfolio.eth_puts_strike = put['strike']
            break
    return f"[ETH] : Ethereum put options to buy on Deribit with the specified strike price. "\
           f"Cost is {trade_setup.portfolio.cost_of_eth_puts}"


# BTC PUTS INPUT -> BTC PUTS TEXT
@app.callback(
    dash.dependencies.Output('btc-puts-txt', 'children'),
    [dash.dependencies.Input('amount-btc-puts-inp', 'value'),
     dash.dependencies.Input('strike-btc-puts', 'value')])
def update_amount_btc_puts(amount_btc_puts, strike_btc_puts):
    trade_setup.portfolio.btc_puts_amount = amount_btc_puts
    for put in trade_setup.starting_parameters.btc_put_options:
        if put['strike'] == strike_btc_puts:
            trade_setup.portfolio.btc_puts_premium = put['underlying_price'] * put['best_ask_price']
            trade_setup.portfolio.btc_puts_strike = put['strike']
            break
    return f"[BTC] : Bitcoin put options to buy on Deribit with the specified strike price. "\
           f"Cost is {trade_setup.portfolio.cost_of_btc_puts}"


def build_plot(resolution=100, btc_max=200000, eth_max=10000):
    eth_prices = [i * eth_max / resolution for i in range(0, resolution + 1)]
    btc_prices = [i * btc_max / resolution for i in range(0, resolution + 1)]
    liq_prices = [trade_setup.calculate_bitmex_eth_liq_price(btc_prices[i]) for i in range(0, resolution + 1)]

    pnl_table = np.zeros((resolution + 1, resolution + 1))
    for eth_index in range(resolution + 1):
        for btc_index in range(resolution + 1):
            trade_setup.set_exit_prices(eth_prices[eth_index], btc_prices[btc_index])
            pnl_table[eth_index, btc_index] = trade_setup.calculate_pnl()

    fig = go.Figure(data=go.Contour(z=pnl_table, x=btc_prices, y=eth_prices,
                                    contours=dict(
                                        start=-1 * trade_setup.bitmex_starting_value,
                                        end=trade_setup.bitmex_starting_value,
                                        size=trade_setup.bitmex_starting_value),
                                    contours_coloring='heatmap'),
                    layout=dict(height=1000))

    fig.add_trace(go.Scatter(x=[trade_setup.starting_parameters.btc_start_price, trade_setup.starting_parameters.btc_start_price,],
                             y=[eth_prices[0], eth_prices[-1]],
                             line=dict(color='black')))
    fig.add_trace(go.Scatter(y=[trade_setup.starting_parameters.eth_quanto_futures_start_price, trade_setup.starting_parameters.eth_quanto_futures_start_price,],
                             x=[btc_prices[0], btc_prices[-1]],
                             line=dict(color='black')))
    fig.add_trace(go.Scatter(y=[trade_setup.starting_parameters.eth_spot_start_price, trade_setup.starting_parameters.eth_spot_start_price,],
                             x=[btc_prices[0], btc_prices[-1]],
                             line=dict(color='black')))
    fig.add_trace(go.Scatter(x=btc_prices, y=liq_prices, line=dict(color="red"), name="BitMEX liquidation"))
    fig.update_xaxes(range=[btc_prices[0], btc_prices[-1]])
    fig.update_yaxes(range=[eth_prices[0], eth_prices[-1]])
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)