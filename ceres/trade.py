from datetime import datetime
DIR_LONG = 1
DIR_SHORT = -1
class Trade(object):
    def __init__(self, symbol, direction=DIR_LONG, number=0, price=0, time=None):
        self.symbol = symbol
        self.direction = direction
        self.number = number
        self.price = price
        self.time = time or datetime.now()

    def apply(self, account):
        if self.direction == DIR_LONG:
            account.update_position(self.symbol, self.number, self.time)
            account.update_cash(self.number * -1 * self.price, self.time)
        else:
            account.update_position(self.symbol, self.number * -1, self.time)
            account.update_cash(self.number * self.price, self.time)
        return True