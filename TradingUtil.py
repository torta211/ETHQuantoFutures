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
            if option_name[-1] == 'C' and self.btc_start_price + 15000 < option['strike'] < 130000:
                option_ticker = requests.get(f"https://www.deribit.com/api/v2/public/ticker?instrument_name={option_name}").json()['result']
                option_ticker['strike'] = option['strike']
                self.btc_call_options.append(option_ticker)
            elif option_name[-1] == 'P' and 18000 < option['strike'] < self.btc_start_price:
                option_ticker = requests.get(f"https://www.deribit.com/api/v2/public/ticker?instrument_name={option_name}").json()['result']
                option_ticker['strike'] = option['strike']
                self.btc_put_options.append(option_ticker)

        eth_options = requests.get("https://www.deribit.com/api/v2/public/get_instruments?currency=ETH&kind=option&expired=false").json()['result']
        eth_options = [option for option in eth_options if "JUN" in option['instrument_name']]
        self.eth_call_options = []
        self.eth_put_options = []
        for option in eth_options:
            option_name = option['instrument_name']
            if option_name[-1] == 'C' and self.eth_spot_start_price + 400 < option['strike'] < 4900:
                option_ticker = requests.get(f"https://www.deribit.com/api/v2/public/ticker?instrument_name={option_name}").json()['result']
                option_ticker['strike'] = option['strike']
                self.eth_call_options.append(option_ticker)
            elif option_name[-1] == 'P' and 570 < option['strike'] < self.eth_spot_start_price:
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
        self.btc_amount_bitmex = 0.2

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

    def calc_range_min(self, btc_prices, eth_prices):
        self.set_exit_prices(eth_exit_price=7500, btc_exit_price=160000)
        if self.calculate_pnl() < 0:
            return -1e9
        self.set_exit_prices(eth_exit_price=600, btc_exit_price=32000)
        if self.calculate_pnl() < 0:
            return -1e9

        min_pnl = 1e9
        for btc_price in btc_prices:
            for eth_price in eth_prices:
                self.set_exit_prices(eth_exit_price=eth_price, btc_exit_price=btc_price)
                pnl = self.calculate_pnl()
                if pnl < min_pnl:
                    min_pnl = pnl
        return min_pnl

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

    def set_optimal_state(self):
        print("optimizing")
        USD_VALUE_ETH = 10000
        btc_prices_range = [35000 + 2500 * i for i in range(26)]
        eth_prices_range = [1400 + 200 * i for i in range(16)]

        BTC_VALUE_ETH = USD_VALUE_ETH / self.starting_parameters.btc_start_price
        SPOT_ETH = round(USD_VALUE_ETH / self.starting_parameters.eth_spot_start_price, 2)
        CONTRACTS_ETH = round(BTC_VALUE_ETH /
                              self.starting_parameters.quanto_multiplier /
                              self.starting_parameters.eth_quanto_futures_start_price)

        self.portfolio.set_eth_contracts_to_short(CONTRACTS_ETH)
        self.portfolio.set_eth_spot_amount(SPOT_ETH)

        BTC_CALL_AMOUNTS = [i / 4 * BTC_VALUE_ETH for i in range(0, 5)]
        ETH_CALL_AMOUNTS = [i / 4 * SPOT_ETH for i in range(0, 5)]
        BTC_PUT_AMOUNTS = [i / 4 * BTC_VALUE_ETH for i in range(0, 5)]
        ETH_PUT_AMOUNTS = [i / 4 * SPOT_ETH for i in range(0, 5)]

        cnt = 0
        iters = len(BTC_CALL_AMOUNTS) * len(ETH_CALL_AMOUNTS) * len(BTC_PUT_AMOUNTS) * len(ETH_PUT_AMOUNTS) * \
            len(self.starting_parameters.btc_call_options) * len(self.starting_parameters.btc_put_options) * \
            len(self.starting_parameters.eth_call_options) * len(self.starting_parameters.eth_put_options)
        maximum_of_range_minimums = -1e9
        optimal = []
        for btc_call in self.starting_parameters.btc_call_options:
            self.portfolio.btc_calls_strike = btc_call['strike']
            self.portfolio.btc_calls_premium = btc_call['underlying_price'] * btc_call['best_ask_price']
            for btc_call_amount in BTC_CALL_AMOUNTS:
                self.portfolio.btc_calls_amount = btc_call_amount

                for btc_put in self.starting_parameters.btc_put_options:
                    self.portfolio.btc_puts_strike = btc_put['strike']
                    self.portfolio.btc_puts_premium = btc_put['underlying_price'] * btc_put['best_ask_price']
                    for btc_put_amount in BTC_PUT_AMOUNTS:
                        self.portfolio.btc_puts_amount = btc_put_amount

                        for eth_call in self.starting_parameters.eth_call_options:
                            self.portfolio.eth_calls_strike = eth_call['strike']
                            self.portfolio.eth_calls_premium = eth_call['underlying_price'] * eth_call['best_ask_price']
                            for eth_call_amount in ETH_CALL_AMOUNTS:
                                self.portfolio.eth_calls_amount = eth_call_amount

                                for eth_put in self.starting_parameters.eth_put_options:
                                    self.portfolio.eth_puts_strike = eth_put['strike']
                                    self.portfolio.eth_puts_premium = eth_put['underlying_price'] * eth_put['best_ask_price']
                                    for eth_put_amount in ETH_PUT_AMOUNTS:
                                        self.portfolio.eth_puts_amount = eth_put_amount

                                        min_pnl_of_range = self.calc_range_min(btc_prices_range, eth_prices_range)
                                        if min_pnl_of_range > maximum_of_range_minimums:
                                            maximum_of_range_minimums = min_pnl_of_range
                                            print(f"\rnew best: BTC CALLS: {btc_call_amount} at {btc_call['strike']} + "
                                                  f"BTC PUTS: {btc_put_amount} at {btc_put['strike']} +"
                                                  f"ETH CALLS: {eth_call_amount} at {eth_call['strike']} +"
                                                  f"ETH PUTS: {eth_put_amount} at {eth_put['strike']} "
                                                  f"PNL = {min_pnl_of_range}")
                                            optimal = [btc_call_amount, btc_call['strike'], btc_call['underlying_price'] * btc_call['best_ask_price'],
                                                       btc_put_amount, btc_put['strike'], btc_put['underlying_price'] * btc_put['best_ask_price'],
                                                       eth_call_amount, eth_call['strike'], eth_call['underlying_price'] * eth_call['best_ask_price'],
                                                       eth_put_amount, eth_put['strike'], eth_put['underlying_price'] * eth_put['best_ask_price']]
                                        cnt += 1
                                        if cnt % 1000 == 0:
                                            print(f"\r{cnt}/{iters}", end='')

        self.portfolio.btc_calls_amount, \
        self.portfolio.btc_calls_strike, \
        self.portfolio.btc_calls_premium, \
        self.portfolio.btc_puts_amount, \
        self.portfolio.btc_puts_strike, \
        self.portfolio.btc_puts_premium, \
        self.portfolio.eth_calls_amount, \
        self.portfolio.eth_calls_strike, \
        self.portfolio.eth_calls_premium, \
        self.portfolio.eth_puts_amount, \
        self.portfolio.eth_puts_strike, \
        self.portfolio.eth_puts_premium = optimal
