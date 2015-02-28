from tixis import app
from flask import request, render_template, url_for, redirect, abort
from bson.objectid import ObjectId
from tixis.model import *
from tixis.program import Program
from core.stock import Stock

class Trade(TixisModel):
    _collection_name = 'trades'
    _fields = [
        OIDField(name="program", optional=False),
        CharField(name="symbol", optional=False),
        TimeField(name="buytime", optional=False),
        PriceField(name="buyprice", optional=False),
        PriceField(name="riskprice", optional=False),
        UIntField(name="amount", optional=False),
        PriceField(name="averagecost", optional=False),

        # for ended trades
        EnumField(name="status", values=('running', 'ended'), optional=False, default="running"),
        TimeField(name="endtime"),
        PriceField(name="finalincome"),
    ]

    def init(self):
        self._stock = None

    @property
    def stock(self):
        if not self._stock:
            self._stock = Stock(self.symbol)
        return self._stock

    @property
    def R(self):
        return abs((self.riskprice - self.averagecost) * self.amount)

    @property
    def income(self):
        return (self.stock.latest_price[0] - self.averagecost) * self.amount

    @property
    def income_R(self):
        return round(self.income/self.R, 2)

@app.route("/program/<pid>/trades")
def trade_list(pid):
    try:
        prog = Program(pid)
    except KeyError:
        abort(404)
    running_trades = Trade.find({'program':ObjectId(pid), 'status':'running'})
    running_symbols = ':'.join([trade.symbol for trade in running_trades])
    ended_trades = Trade.find({'program':ObjectId(pid), 'status':'ended'})
    return render_template('trade_list.html', prog=prog, running_trades=running_trades, ended_trades=ended_trades, running_symbols=running_symbols)

@app.route("/program/<pid>/addtrade", methods=['POST','GET'])
def trade_add(pid):
    if request.method == 'GET':
        try:
            prog = Program(pid)
        except KeyError:
            abort(404)
        return render_template('trade_add.html', prog=prog, error_show='hidden')
    elif request.method == 'POST':
        new_trade = {
            'program': pid,
            'symbol': request.form['symbol'],
            'buytime': request.form['buytime'],
            'buyprice': request.form['buyprice'],
            'riskprice': request.form['riskprice'],
            'amount': request.form['amount'],
            'averagecost': request.form['averagecost'],

            'status': request.form['status'],
            'endtime': request.form['endtime'] or None,
            'finalincome': request.form['finalincome'] or None,
        }
        try:
            tr = Trade.new(**new_trade)
        except ValidationError, e:
            return render_template('trade_add.html', error_show='', error_msg=str(e))
        return redirect(url_for('program_detail', oid=pid))
