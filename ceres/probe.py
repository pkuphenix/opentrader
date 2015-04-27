from common.utils import gen_time, Observable
from common.db import db_ot
from datetime import datetime, timedelta, date, time as daytime
import time
from collections import OrderedDict
from core.ticker import Ticker,TradeCalendar
from core.stock import Stock
from core.query import QuerySet

class ProbeImplementError(Exception):
    pass

class Probe(Observable):
    def __init__(self, *args, **kwargs):
        self.entries = OrderedDict() # each entry is an ordered dict of {<symbol>:<attr_dict>}
                                     # and <attr_dict> at least contains three keys:
                                     # 'time': detected(appended) time
                                     # 'start': time to start processing in this probe (now >= start)
                                     # 'end': time to remove the entry (only process the entry when now < end)
        self.entry_auto_all = False
        self.entry_auto_all_query = True # automatically query all symbols if entry_auto_all is True
        self.ticker = None
        self.initob()
        self.init(*args, **kwargs)

    def init(self, **kwargs):
        pass # to be overwritten by sub classes

    def append_entry(self, symbol, time, delay=timedelta(0), life=timedelta(days=1), **kwargs):
        attr = kwargs
        attr['time'] = time
        attr['start'] = time + delay
        attr['end'] = attr['start'] + life
        self.entries[symbol] = attr

    @property
    def alive_entries(self):
        rtn = OrderedDict() # a copy of alive entries
        for symbol, attr in self.entries.iteritems():
            if 'end' in attr and self.ticker.now >= attr['end']:
                del self.entries[symbol]

        for symbol, attr in self.entries.iteritems():
            if 'start' in attr:
                if self.ticker.now >= attr['start']:
                    rtn[symbol] = attr
            else:
                rtn[symbol] = attr
        return rtn

    # get all available k_day entries
    # from database for specific date
    def _get_all_entries(self, d):
        assert type(d) is date
        res = db_ot.xueqiu_k_day.find({'time':datetime(d.year, d.month, d.day)})
        for each in list(res):
            self.append_entry(each['symbol'], self.ticker.now)

    def set_entry_auto_all(self, autoquery=True):
        self.entry_auto_all = True
        self.entry_auto_all_query = autoquery

    def _handle_entry_from_source(self, delay, life):
        def func(e):
            for each in e.symbols:
                self.append_entry(each, e.time, delay, life)
        return func

    def set_entry_source(self, probe, delay=timedelta(0), life=timedelta(days=1)):
        probe.subscribe('probe-detect', getattr(self, '_handle_entry_from_source')(delay, life))

    def bind_ticker(self, ticker):
        self.ticker = ticker
        if hasattr(self, '_day_close'):
            ticker.subscribe('day-close', getattr(self, 'day_close'))

    def day_close(self, ticker_event):
        if self.entry_auto_all and self.entry_auto_all_query:
            self._get_all_entries(ticker_event.source.now.date())

        self._day_close(ticker_event, self.alive_entries)

    def _day_close(self, ticker_event, entries):
        raise ProbeImplementError


class PercentProbe(Probe):
    def init(self, waterline=9, operation='$gte'):
        self.waterline = waterline
        self.operation = operation

    def _day_close(self, ticker_event, entries):
        time = ticker_event.source.now
        date = time.date()
        if self.entry_auto_all:
            res = db_ot.xueqiu_k_day.find({'time':datetime(date.year, date.month, date.day), 'percent':{self.operation:self.waterline}})
            symbols = []
            for each in res:
                symbols.append(each['symbol'])
            if symbols:
                self.fire('probe-detect', symbols=symbols, time=time)
        else:
            symbols = []
            for symbol,attr in entries.iteritems():
                #print symbol,attr
                res = db_ot.xueqiu_k_day.find_one({'symbol':symbol, 'time':datetime(date.year, date.month, date.day), 'percent':{self.operation:self.waterline}})
                if res:
                    symbols.append(symbol)
            if symbols:
                self.fire('probe-detect', symbols=symbols, time=time)
        return

class FilterProbe(Probe):
    def init(self, script=''):
        self.script = script

    def _day_close(self, ticker_event, entries):
        if self.entry_auto_all:
            q = QuerySet.all(ticker=ticker_event.source).run_script(self.script)
        else:
            stocks = []
            for symbol in entries.keys:
                stocks.append(Stock(symbol, ticker=ticker_event.source))
            q = QuerySet(stocks).run_script(self.script)
        
        symbols = []
        for each in q.stocks:
            symbols.append(each.symbol)
        self.fire('probe-detect', symbols=symbols, time=ticker_event.source.now)

class Newhigh55Probe(Probe):
    def _day_close(self, ticker_event, entries):
        time = ticker_event.source.now
        date = time.date()
        if self.entry_auto_all:
            res = db_ot.xueqiu_k_day.find({'time':datetime(date.year, date.month, date.day), '$where':'this.close>this.high55_last'})
        if res:
            symbols = []
            for each in res:
                symbols.append(each['symbol'])
            self.fire('probe-detect', symbols=symbols, time=ticker_event.source.now)



class PercentRecorder(object):
    def __init__(self, name='', ignore=0):
        self.count = 0
        self.sum = 0
        self.name = name
        self.ignore = ignore

    def eat_ignore(self):
        self.ignore -= 1

    def record(self, percent):
        if self.ignore > 0:
            return
        self.count += 1
        self.sum += percent

    def show(self):
        if self.count > 0:
            print '%s - recording result: total count %u, average %f' % (self.name, self.count, self.sum/self.count)
        else:
            print '%s - no records' % (self.name)

def atest_probe():
    ticker = Ticker(begin=gen_time("2015-01-01 00:00:00"), end=gen_time("2015-03-01 00:00:00"))
    def ticker_printer(e):
        print e.source.now.date()
    ticker.subscribe('day-close', ticker_printer)

    # First probe -- percent > 9
    p = PercentProbe(4)
    p.bind_ticker(ticker)
    def probe_detected(e):
        print e.symbols, e.time
    p.set_entry_auto_all(autoquery=False)
    #p.subscribe('probe-detect', probe_detected)

    # Second probe -- percent < -9
    q = PercentProbe(-9, "$lte")
    q.bind_ticker(ticker)
    q.set_entry_source(p, delay=timedelta(days=1))
    q.subscribe('probe-detect', probe_detected)

    ticker.run()

def test_filter_probe():
    ticker = Ticker(begin=gen_time("2015-01-01 00:00:00"), end=gen_time("2015-03-09 00:00:00"))
    def ticker_printer(e):
        print e.source.now.date()
    ticker.subscribe('day-close', ticker_printer)
    p = FilterProbe(script='filter(":kday::high","$gte",":kday::high55").filter(":kday::volume","$gte",mul(":kday|today|-1::volume",2))')
    #p = FilterProbe(script='filter(":kday|today|-2::percent","$gte",9).filter(":kday|today|-1::high","$gt",":kday|today|-1::close").filter(":kday|today|-1::open","$gt",":kday|today|-1::low").filter(":kday|today|-1::percent","$gt",0).filter(":kday::close","$gte",":kday|today|-1::high")')
    #p = FilterProbe(script='filter(":kday::percent","$gte",0).filter(":kday::percent","$lte",4).filter(":kday::volume","$gte",mul(":kday|today|-1::volume",2)).filter(":kday::volume","$lte",mul(":kday|today|-1::volume",3))')
    p.bind_ticker(ticker)
    p.set_entry_auto_all(autoquery=False)

    gr = PercentRecorder('global')
    def probe_detected(e):
        tom_date = TradeCalendar.get_date(e.time.date(),1)
        dr = PercentRecorder('daily')
        # get the percent of the second day
        for symbol in e.symbols:
            tomk0 = db_ot.xueqiu_k_day.find_one({'symbol':symbol,'time':datetime(e.time.date().year,e.time.date().month,e.time.date().day)})
            tomk = db_ot.xueqiu_k_day.find_one({'symbol':symbol,'time':datetime(tom_date.year,tom_date.month,tom_date.day)})
            if tomk:
                dr.record(tomk['percent'])
                gr.record(tomk['percent'])
                #dr.record((tomk['open']-tomk0['close'])/tomk0['close']*100)
                #gr.record((tomk['open']-tomk0['close'])/tomk0['close']*100)
        dr.show()
        gr.show()
    p.subscribe('probe-detect', probe_detected)
    ticker.run()

def atest_high55_probe():
    ticker = Ticker(begin=gen_time("2015-01-01 00:00:00"), end=gen_time("2015-03-01 00:00:00"))
    def ticker_printer(e):
        print e.source.now.date()
    ticker.subscribe('day-close', ticker_printer)

    p = Newhigh55Probe()
    p.bind_ticker(ticker)
    def probe_detected(e):
        print e.symbols, e.time
    p.set_entry_auto_all(autoquery=False)
    p.subscribe('probe-detect', probe_detected)
    ticker.run()
