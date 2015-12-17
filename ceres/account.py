# virtual account to test invest policies
from datetime import datetime, timedelta
import math
from opentrader.ceres.trade import *

class Account(object):
    def __init__(self, initial, establish=None, currency='CNY'):
        self._initial = initial
        self._currency = currency
        self._establish = establish or datetime.now()

        self._trades = []
        self._cash = self._initial
        self._net_asset = self._initial
        self._net_value = 1.0
        self._cost = self._initial
        self._positions = {} # {"symbol": <number>}
        self._quotes = {} # {"symbol": <quote>}

        self.history_positions = [(self._establish, self._positions.copy())] # [(<time>, <value>), ...]
        self.history_net_asset = [(self._establish, self._net_asset)] # [(<time>, <value>), ...]
        self.history_net_value = [(self._establish, self._net_value)] # [(<time>, <value>), ...]
        self.history_cost      = [(self._establish, self._cost)] # [(<time>, <value>), ...]
        self.history_cash      = [(self._establish, self._cash)] # [(<time>, <value>), ...]
        self.history_market_asset = [(self._establish, 0)]

    @property
    def cash(self):
        return self._cash

    # calculate market_asset/net_asset/net_value
    def _calculate(self, time):
        market_asset = 0
        for (symbol, number) in self._positions.items():
            market_asset += number * self._quotes.get(symbol, 0)

        new_net_asset = self._cash + market_asset
        self.history_net_value.append((time, self._net_value))
        self._net_value = self._net_value * new_net_asset / self._net_asset
        
        self.history_market_asset.append((time, market_asset))
        self.history_net_asset.append((time, self._net_asset))
        self._net_asset = new_net_asset

    ############################
    # public interfaces for users
    ############################
    # all updates to the account are implemented by trades
    # as implemented in each trade's "apply" function.
    def trade(self, trade):
        if (trade.apply(self)):
            # trade succeeds, push into trade history
            self._trades.append(trade)
            return True
        else:
            return False

    def transfer(self, amount, time):
        self.update_cash(amount, time)
        self.history_cost.append((time, self._cost))
        self._cost += amount

    def update_quotes(self, quote_dict, time):
        for (symbol, quote) in quote_dict.items():
            self._quotes[symbol] = quote
        self._calculate(time)

    # components: {"SH001001": 0.6, "cash": 0.4}
    def rebalance(self, components, time):
        new_positions = {}
        for (symbol, comp) in components.items():
            if symbol == 'cash':
                continue
            new_positions[symbol] = float(math.floor(comp * self._net_asset / self._quotes[symbol]))

        for (symbol, position) in self._positions.items():
            new_position = new_positions.get(symbol, 0.0)
            if new_position > position:
                self.trade(Trade(symbol, DIR_LONG, new_position-position, self._quotes[symbol], time))
            elif new_position < position:
                self.trade(Trade(symbol, DIR_SHORT, position-new_position, self._quotes[symbol], time))
        return True

    # calculate based on history_net_value
    def avr_annual_return_rate(self):
        days = (self.history_net_value[-1][0] - self.history_net_value[0][0]).days
        if days == 0:
            return 0
        years = float(days) / 365.0
        return math.pow((self.history_net_value[-1][1] / self.history_net_value[0][1]), 1/years) - 1

    def maximum_dropdown(self):
        (peak_time, peak) = self.history_net_value[0]
        (valley_time, valley) = self.history_net_value[0]
        max_dropdown = 0
        max_dropdown_time = (None, None)
        for val in self.history_net_value:
            if val[1] > peak: # new high
                (peak_time, peak) = val
                (valley_time, valley) = val # recount the valley
            if val[1] < valley:
                (valley_time, valley) = val
                if (1 - valley / peak) > max_dropdown:
                    max_dropdown = (1 - valley / peak)
                    max_dropdown_time = (peak_time, valley_time)
        return (max_dropdown, max_dropdown_time[0], max_dropdown_time[1])


        
    ############################
    # public interfaces that can be updated by trades
    ############################
    def update_position(self, symbol, number, time):
        try:
            self._positions[symbol] += number
        except KeyError:
            self._positions[symbol] = number

    def update_cash(self, amount, time):
        self.history_cash.append((time, self._cash))
        self._cash += amount



