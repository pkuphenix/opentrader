from opentrader.tixis import app
from flask import request, render_template, url_for, redirect, abort
from bson.objectid import ObjectId
from opentrader.tixis.model import *
from opentrader.tixis.program import Program
from opentrader.core.stock import Stock
from opentrader.tixis.session import getuser

class Trade(TixisModel):
    _collection_name = 'trades'
    _fields = [
        OIDField(name="program", optional=False),
        CharField(name="symbol", optional=False),
        TimeField(name="buytime", optional=True),
        PriceField(name="buyprice", optional=True),
        PriceField(name="riskprice", optional=True),
        UIntField(name="amount", optional=True),
        PriceField(name="averagecost", optional=True),

        # for ended trades
        EnumField(name="status", values=('watch','running', 'ended'), optional=False, default="running"),
        TimeField(name="endtime"),
        PriceField(name="sellprice"),
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

    @property
    def finalincome(self):
        if self.sellprice is not None:
            return (self.sellprice - self.averagecost) * self.amount
        else:
            return 0

    @property
    def finalincome_R(self):
        return round(self.finalincome/self.R, 2)

    @property
    def url(self):
        return url_for('trade_edit', pid=self.program, tid=self.oid)

@app.route("/program/<pid>/trades")
def trade_list(pid):
    user = getuser()
    if not user:
        return redirect(url_for('login'))
    try:
        prog = Program(pid)
    except KeyError:
        abort(404)
    running_trades = Trade.find({'program':ObjectId(pid), 'status':'running'})
    running_symbols = ':'.join([trade.symbol for trade in running_trades])
    ended_trades = Trade.find({'program':ObjectId(pid), 'status':'ended'})
    ended_symbols = ':'.join([trade.symbol for trade in ended_trades])
    watch_trades = Trade.find({'program':ObjectId(pid), 'status':'watch'})
    watch_symbols = ':'.join([trade.symbol for trade in watch_trades])
    total_income = 0
    for trade in running_trades:
        total_income += trade.income
    for trade in ended_trades:
        total_income += trade.finalincome
    return render_template('trade_list.html', prog=prog, total_income=total_income,
                           running_trades=running_trades, ended_trades=ended_trades, watch_trades=watch_trades,
                           running_symbols=running_symbols, ended_symbols=ended_symbols, watch_symbols=watch_symbols)

@app.route("/program/<pid>/addtrade", methods=['POST','GET'])
def trade_add(pid):
    user = getuser()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'GET':
        try:
            prog = Program(pid)
        except KeyError:
            abort(404)
        return render_template('trade_add.html', prog=prog, error_show='hidden')
    elif request.method == 'POST':
        try:
            prog = Program(pid)
        except KeyError:
            abort(404)
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
            'sellprice': request.form['sellprice'] or None,
        }
        try:
            tr = Trade.new(**new_trade)
        except ValidationError as e:
            return render_template('trade_add.html', error_show='', error_msg=str(e), prog=prog)
        return redirect(url_for('program_detail', oid=pid))

@app.route("/program/<pid>/edittrade/<tid>", methods=['POST','GET'])
def trade_edit(pid, tid):
    user = getuser()
    if not user:
        return redirect(url_for('login'))
    try:
        prog = Program(pid)
    except KeyError:
        abort(404)
    try:
        trade = Trade(tid)
    except KeyError:
        abort(404)
    if request.method == 'GET':
        return render_template('trade_edit.html', prog=prog, trade=trade, error_show='hidden')
    elif request.method == 'POST':
        new_info = {
            'program': pid,
            'symbol': request.form['symbol'],
            'buytime': request.form['buytime'],
            'buyprice': request.form['buyprice'],
            'riskprice': request.form['riskprice'],
            'amount': request.form['amount'],
            'averagecost': request.form['averagecost'],

            'status': request.form['status'],
            'endtime': request.form['endtime'] or None,
            'sellprice': request.form['sellprice'] or None,
        }
        try:
            trade.update(**new_info)
        except ValidationError as e:
            return render_template('trade_edit.html', prog=prog, trade=trade, error_show='', error_msg=str(e))
        return redirect(url_for('program_detail', oid=pid))

