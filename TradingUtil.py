import requests
import dash_html_components as html


class StartingPrices:
    quanto_multiplier = 0.000001

    def __init__(self):
        self.btc_start_price = 50000
        self.eth_spot_start_price = 1600
        self.eth_quanto_futures_start_price = 2200
        self.btc_call_options = []
        self.btc_put_options = []
        self.eth_call_options = []
        self.eth_put_options = []

    def query(self):
        bitmex_xbtusd = requests.get("https://www.bitmex.com/api/v1/quote?symbol=XBTUSD&count=1&reverse=true").json()[0]
        self.btc_start_price = round(bitmex_xbtusd['bidPrice'], 2)

        bitmex_ethusdm21 = requests.get("https://www.bitmex.com/api/v1/quote?symbol=ETHUSDM21&count=1&reverse=true").json()[0]
        self.eth_quanto_futures_start_price = round(bitmex_ethusdm21['bidPrice'], 2)

        binance_ethusd = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT").json()
        self.eth_spot_start_price = round(float(binance_ethusd['price']), 2)

        btc_options = requests.get("https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option&expired=false").json()['result']
        btc_options = [option for option in btc_options if "JUN" in option['instrument_name']]
        self.btc_call_options = []
        self.btc_put_options = []
        for option in btc_options:
            option_name = option['instrument_name']
            if option_name[-1] == 'C' and option['strike'] > self.btc_start_price - 5000:
                option_ticker = requests.get(f"https://www.deribit.com/api/v2/public/ticker?instrument_name={option_name}").json()['result']
                option_ticker['strike'] = option['strike']
                self.btc_call_options.append(option_ticker)
            elif option_name[-1] == 'P' and option['strike'] < self.btc_start_price + 5000:
                option_ticker = requests.get(f"https://www.deribit.com/api/v2/public/ticker?instrument_name={option_name}").json()['result']
                option_ticker['strike'] = option['strike']
                self.btc_put_options.append(option_ticker)

        eth_options = requests.get("https://www.deribit.com/api/v2/public/get_instruments?currency=ETH&kind=option&expired=false").json()['result']
        eth_options = [option for option in eth_options if "JUN" in option['instrument_name']]
        self.eth_call_options = []
        self.eth_put_options = []
        for option in eth_options:
            option_name = option['instrument_name']
            if option_name[-1] == 'C' and option['strike'] > self.eth_spot_start_price - 200:
                option_ticker = requests.get(f"https://www.deribit.com/api/v2/public/ticker?instrument_name={option_name}").json()['result']
                option_ticker['strike'] = option['strike']
                self.eth_call_options.append(option_ticker)
            elif option_name[-1] == 'P' and option['strike'] < self.eth_spot_start_price + 200:
                option_ticker = requests.get(f"https://www.deribit.com/api/v2/public/ticker?instrument_name={option_name}").json()['result']
                option_ticker['strike'] = option['strike']
                self.eth_put_options.append(option_ticker)

    @property
    def starting_premium(self):
        return round(((self.eth_quanto_futures_start_price / self.eth_spot_start_price) - 1) * 100)

    @property
    def html_summary(self):
        return ["Starting prices are:", html.Br(),
                f" · BTC: {self.btc_start_price} [USD],",
                f" · Ethereum spot: {self.eth_spot_start_price} [USD],",
                f" · Ethereum quanto futures: {self.eth_quanto_futures_start_price} [USD],",
                f" · {self.starting_premium}% starting premium"]


class ExitPrices:
    def __init__(self, eth_exit_price=1800, btc_exit_price=50000, premium_exit=0):
        self.eth_exit_price = eth_exit_price
        self.btc_exit_price = btc_exit_price
        self.premium_exit = premium_exit

    @property
    def eth_futures_exit_price(self):
        return self.eth_exit_price * (1 + self.premium_exit)


class Portfolio:
    def __init__(self):
        self.eth_spot_amount = 0
        self.eth_quanto_futures_contracts_shorted = 0
        self.btc_amount_bitmex = 1

        self.eth_calls_amount = 0
        self.eth_calls_premium = 0
        self.eth_calls_strike = 1000000

        self.btc_calls_amount = 0
        self.btc_calls_premium = 0
        self.btc_calls_strike = 1000000

        self.eth_puts_amount = 0
        self.eth_puts_premium = 0
        self.eth_puts_strike = 0

        self.btc_puts_amount = 0
        self.btc_puts_premium = 0
        self.btc_puts_strike = 0

    @property
    def cost_of_calls(self):
        return self.cost_of_eth_calls + self.cost_of_btc_calls

    @property
    def cost_of_eth_calls(self):
        return self.eth_calls_amount * self.eth_calls_premium

    @property
    def cost_of_btc_calls(self):
        return self.btc_calls_amount * self.btc_calls_premium

    @property
    def cost_of_puts(self):
        return self.cost_of_eth_puts + self.cost_of_btc_puts

    @property
    def cost_of_eth_puts(self):
        return self.eth_puts_amount * self.eth_puts_premium

    @property
    def cost_of_btc_puts(self):
        return self.btc_puts_amount * self.btc_puts_premium

    def set_eth_spot_amount(self, amount):
        self.eth_spot_amount = amount

    def set_btc_amount_bitmex(self, amount):
        self.btc_amount_bitmex = amount

    def set_eth_contracts_to_short(self, amount):
        self.eth_quanto_futures_contracts_shorted = amount


class TradeSetup:
    def __init__(self):
        self.starting_parameters = StartingPrices()
        self.exit_parameters = ExitPrices()
        self.portfolio = Portfolio()

    def set_exit_prices(self, eth_exit_price, btc_exit_price):
        self.exit_parameters.eth_exit_price = eth_exit_price
        self.exit_parameters.btc_exit_price = btc_exit_price

    def set_exit_premium(self, exit_premium):
        self.exit_parameters.premium_exit = exit_premium

    def calculate_pnl(self):
        eth_spot_pnl_usd = self.portfolio.eth_spot_amount * \
                           (self.exit_parameters.eth_exit_price - self.starting_parameters.eth_spot_start_price)

        eth_quanto_futures_price_movement = self.exit_parameters.eth_futures_exit_price - self.starting_parameters.eth_quanto_futures_start_price
        eth_quanto_futures_pnl_btc = self.portfolio.eth_quanto_futures_contracts_shorted * \
                                     (eth_quanto_futures_price_movement * -1 * self.starting_parameters.quanto_multiplier)
        eth_quanto_futres_pnl_usd = eth_quanto_futures_pnl_btc * self.exit_parameters.btc_exit_price

        # we assume the btc holding on bitmex to be fully hedged at start, so that contributes 0

        # calculate the profit of the CALLS
        calls_profit = 0
        if self.exit_parameters.eth_exit_price > self.portfolio.eth_calls_strike:
            calls_profit += self.portfolio.eth_calls_amount * \
                            (self.exit_parameters.eth_exit_price - self.portfolio.eth_calls_strike)
        if self.exit_parameters.btc_exit_price > self.portfolio.btc_calls_strike:
            calls_profit += self.portfolio.btc_calls_amount * \
                            (self.exit_parameters.btc_exit_price - self.portfolio.btc_calls_strike)

        # calculate the profit of the PUTS
        puts_profit = 0
        if self.exit_parameters.eth_exit_price < self.portfolio.eth_puts_strike:
            puts_profit += self.portfolio.eth_puts_amount * \
                            (self.portfolio.eth_puts_strike - self.exit_parameters.eth_exit_price)
        if self.exit_parameters.btc_exit_price < self.portfolio.btc_puts_strike:
            puts_profit += self.portfolio.btc_puts_amount * \
                            (self.portfolio.btc_puts_strike - self.exit_parameters.btc_exit_price)
        return eth_spot_pnl_usd + eth_quanto_futres_pnl_usd + calls_profit - self.portfolio.cost_of_calls + puts_profit - self.portfolio.cost_of_puts

    def calculate_bitmex_eth_liq_price(self, for_btc_price):
        # lost_BTC = contracts * price_move * multiplier
        # bitmex_BTC = contracts * (liq - entry) * multiplier
        # liq = bitmex_BTC / multiplier / contracts + entry
        try:
            btc_available = self.portfolio.btc_amount_bitmex * self.starting_parameters.btc_start_price / for_btc_price
            return self.starting_parameters.eth_quanto_futures_start_price + \
                   (btc_available / self.starting_parameters.quanto_multiplier / self.portfolio.eth_quanto_futures_contracts_shorted)
        except ZeroDivisionError:
            return 1000000


    @property
    def eth_spot_value(self):
        return round(self.portfolio.eth_spot_amount * self.starting_parameters.eth_spot_start_price, 2)

    @property
    def eth_quanto_futures_value(self):
        return self.portfolio.eth_quanto_futures_contracts_shorted * \
               self.starting_parameters.eth_quanto_futures_start_price * \
               self.starting_parameters.quanto_multiplier * \
               self.starting_parameters.btc_start_price

    @property
    def eth_quanto_futures_btc_value(self):
        return self.portfolio.eth_quanto_futures_contracts_shorted * \
               self.starting_parameters.eth_quanto_futures_start_price * \
               self.starting_parameters.quanto_multiplier

    @property
    def bitmex_starting_value(self):
        return self.portfolio.btc_amount_bitmex * self.starting_parameters.btc_start_price