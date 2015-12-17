from .script import *
from .stock import Stock, StockDataNotExist
from .ticker import Ticker
from common.db import db_ot
from common.utils import Operator,gen_time
from datetime import datetime
import time
import collections
from functools import reduce

def parse_ref_val(ref, stock):
    if type(ref) in (str, str) and ref.startswith(':'):
        (path, key) = (ref[1:].split('::') + [None])[:2]
        path = path.split('|')
        attr = path[0]
        args = path[1:]
        if key is None:
            return getattr(stock, attr)(*args)
        else:
            try:
                res = getattr(stock, attr)(*args)
                if type(res) is list:
                    return [val[key] for val in res]
                else:
                    return res[key]
            except KeyError:
                raise StockDataNotExist('Key does not exist: %s' % key)
    elif isinstance(ref, collections.Callable):
        return ref(stock)
    else:
        return ref

class QuerySet(object):
    def __init__(self, stocks=[]):
        self.stocks = stocks

    # Case 1: filter("ref"/val, operator, "ref"/val)
    # Case 2: filter("ref"/val, operator)
    # Case 3: filter("ref"/val, "ref"/val) -- equals
    # Case 4: filter("ref"/val) -- must be True/False
    def filter(self, val1=None, oper=None, val2=None):
        assert val1 is not None
        #print 'filter called %s %s %s' % (val1, oper, val2)
        # Case 4:
        if oper is None and val2 is None:
            rtn = []
            for stock in self.stocks:
                try:
                    a = parse_ref_val(val1, stock)
                except StockDataNotExist:
                    continue
                if a is True:
                    rtn.append(stock)
            return QuerySet(rtn)
        elif val2 is None:
            # Case 2
            if type(oper) in (str, str) and oper.startswith('$'):
                # this is an operator
                oper_func = getattr(Operator, oper[1:])
                rtn = []
                for stock in self.stocks:
                    try:
                        a = parse_ref_val(val1, stock)
                    except StockDataNotExist:
                        continue
                    if oper_func(a):
                        rtn.append(stock)
                return QuerySet(rtn)
            # Case 3
            else:
                rtn = []
                for stock in self.stocks:
                    try:
                        a = parse_ref_val(val1, stock)
                        b = parse_ref_val(oper, stock)
                    except StockDataNotExist:
                        continue
                    if a == b:
                        rtn.append(stock)
                return QuerySet(rtn)
        # Case 1
        else:
            # oper must be an operator
            assert oper.startswith('$'), 'Invalid operation %s!' % oper
            oper_func = getattr(Operator, oper[1:])
            rtn = []
            for stock in self.stocks:
                try:
                    a = parse_ref_val(val1, stock)
                    b = parse_ref_val(val2, stock)
                except StockDataNotExist:
                    continue
                if oper_func(a, b):
                    rtn.append(stock)
            return QuerySet(rtn)
        return QuerySet([])

    def orderby(self, ref, reverse=None):
        assert ref is not None
        def parse_ref_val_with_exception(ref, stock):
            try:
                return parse_ref_val(ref, stock)
            except StockDataNotExist:
                return None
        self.stocks.sort(key=lambda stock: parse_ref_val_with_exception(ref, stock), reverse=True if reverse is not None else False)
        return self

    def limit(self, count=0):
        #assert 0, "%d" % count
        return QuerySet(self.stocks[:int(count)])

    def groupby(self):
        pass

    def count(self):
        return len(self.stocks)

    def __str__(self):
        return 'QuerySet(%s)' % str(self.stocks)

    def __repr__(self):
        return self.__str__()

    def run_script(self, script):
        parser = OTYacc(self, QuerySet)
        parser.build()
        return parser.parse(script)

    _cached_all = None
    _cached_all_time = time.time()
    @staticmethod
    def all(ticker=None):
        if ticker is None:
            if time.time() - QuerySet._cached_all_time < 60 and QuerySet._cached_all is not None:
                return QuerySet._cached_all

            infos = [info for info in db_ot.xueqiu_info.find() if not (info['symbol'].startswith("SH000") or info['symbol'].startswith("SH900") or info['symbol'].startswith("PRE") or info['symbol'].startswith("SZ399"))]
            today = datetime.today()
            today = datetime(today.year, today.month, today.day)
            instants = [instant for instant in db_ot.xueqiu_instant.find({'date':today})]
            stocks = []
            stock_instant_dict = {}

            for each_instant in instants:
                stock_instant_dict[each_instant['symbol']] = each_instant

            for each in infos:
                stocks.append(Stock(each['symbol'], each, stock_instant_dict.get(each['symbol'], None), initialized=True, ticker=ticker))
            
            rtn = QuerySet(stocks)
            QuerySet._cached_all_time = time.time()
            QuerySet._cached_all = rtn
            return rtn
        else:
            today = datetime.today()
            today = datetime(today.year, today.month, today.day)
            infos = [info for info in db_ot.xueqiu_info.find() if not (info['symbol'].startswith("SH000") or info['symbol'].startswith("SH900") or info['symbol'].startswith("PRE") or info['symbol'].startswith("SZ399"))]
            instants = [instant for instant in db_ot.xueqiu_instant.find({'date':today})]
            stocks = []
            stock_instant_dict = {}
            stock_info_dict = {}

            for each_info in infos:
                stock_info_dict[each_info['symbol']] = each_info

            for each_instant in instants:
                stock_instant_dict[each_instant['symbol']] = each_instant

            date = ticker.now.date()
            kdays = [kday for kday in db_ot.xueqiu_k_day.find({'time':datetime(date.year,date.month,date.day)}) if not (info['symbol'].startswith("SH000") or info['symbol'].startswith("SH900") or info['symbol'].startswith("PRE") or info['symbol'].startswith("SZ399"))]
            for each in kdays:
                stocks.append(Stock(each['symbol'], stock_info_dict.get(each['symbol'], None), stock_instant_dict.get(each['symbol'], None), initialized=True, ticker=ticker))
            rtn = QuerySet(stocks)
            return rtn

    @staticmethod
    def merge(qsa, qsb):
        stocks = {}
        for each in qsa.stocks:
            stocks[each.symbol] = each
        for each in qsb.stocks:
            if each.symbol not in stocks:
                stocks[each.symbol] = each
        return QuerySet(list(stocks.values()))

    @staticmethod
    def plus(vala, valb):
        def inner(stock):
            a = parse_ref_val(vala, stock)
            b = parse_ref_val(valb, stock)
            return float(a)+float(b)
        return inner

    @staticmethod
    def minus(vala, valb):
        def inner(stock):
            a = parse_ref_val(vala, stock)
            b = parse_ref_val(valb, stock)
            return float(a)-float(b)
        return inner

    @staticmethod
    def mul(vala, valb):
        def inner(stock):
            a = parse_ref_val(vala, stock)
            b = parse_ref_val(valb, stock)
            return float(a)*float(b)
        return inner

    @staticmethod
    def div(vala, valb):
        def inner(stock):
            a = parse_ref_val(vala, stock)
            b = parse_ref_val(valb, stock)
            if float(b) == 0:
                raise StockDataNotExist('division by zero')
            return float(a)/float(b)
        return inner

    @staticmethod
    def max(vals):
        def inner(stock):
            l = parse_ref_val(vals, stock)
            return max(l)
        return inner

    @staticmethod
    def min(vals):
        def inner(stock):
            l = parse_ref_val(vals, stock)
            return min(l)
        return inner

    @staticmethod
    def avr(vals):
        def inner(stock):
            l = parse_ref_val(vals, stock)
            return reduce(lambda x, y: x + y, l) / float(len(l))
        return inner

class TestQuerySet(object):
    def test_all(self):
        assert len(QuerySet.all().stocks) > 2000

    def test_filter(self):
        all = QuerySet.all()
        assert all.filter(':info::symbol', 'SZ002736').count() == 1
        assert all.filter(':info::current', '$lt', 3).filter(':info::current', '$gt', 0).count() < 100

    def test_script(self):
        all = QuerySet.all()
        assert all.run_script('filter(":info::symbol", "SZ002736")').count() == 1
        assert all.run_script('merge(filter(":info::symbol", "SZ002736"), filter(":info::symbol", "SZ002738"))').count() == 2
        assert all.run_script('filter(":instant::high52week", "$gt", 100).orderby(":info::current", "reverse")').count() < 50
        #print all.run_script('filter(":instant::high","$gte",":instant::high52week").orderby(":instant::symbol")')
        #print all.run_script('filter(":kday|2015-03-13::atr20","$gt",0).orderby(div(":kday|2015-03-13::atr20",":instant::current")).limit(10)')
        #print all.run_script('filter(max(":kdays|2015-03-13|-30::volume"),"$lt",":instant::volume")')
        
        
        ticker = Ticker(begin=gen_time("2015-01-01 00:00:00"), end=gen_time("2015-02-01 00:00:00"))
        def every_day_end(e):
            print(e.source.now)
            print(QuerySet.all(ticker=ticker).run_script('filter(":kday|today|-1::percent","$gte",4).filter(":kday::percent","$lte",-9)'))
        ticker.subscribe('day-close', every_day_end)
        ticker.run()
        

        

