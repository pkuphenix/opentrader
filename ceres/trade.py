class Trade(object):
    def __init__(self, symbol):
        self.symbol = symbol
        self.status = 0

    def buy(self, time, price, risk):
        self.buy_time = time
        self.buy_price = price
        self.initial_risk = risk
        self.status = 1

    def sell(self, time, price):
        self.sell_time = time
        self.sell_price = price
        self.profit_percent = (self.sell_price - self.buy_price)/self.buy_price*100
        self.profit_rtimes = (self.sell_price - self.buy_price)/self.initial_risk
        self.hold_days = (self.sell_time - self.buy_time).days
        self.status = 2


class TradeTracker(object):
    def __init__(self):
        self.trades = []

    def append_trade(self, trade):
        self.trades.append(trade)