from script import *
from stock import *
from common.db import db_ot
from common.utils import Operator
from datetime import datetime
import time

def parse_ref_val(ref, stock):
    if type(ref) in (str, unicode) and ref.startswith(':'):
        (path, key) = (ref[1:].split('::') + [None])[:2]
        path = path.split('|')
        attr = path[0]
        args = path[1:]
        if key is None:
            return getattr(stock, attr)(*args)
        else:
            try:
                return getattr(stock, attr)(*args)[key]
            except KeyError:
                raise StockDataNotExist('Key does not exist: %s' % key)
    elif callable(ref):
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
            if type(oper) in (str, unicode) and oper.startswith('$'):
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
    def all():
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
            stocks.append(Stock(each['symbol'], each, stock_instant_dict.get(each['symbol'], None), initialized=True))
        
        rtn = QuerySet(stocks)
        QuerySet._cached_all_time = time.time()
        QuerySet._cached_all = rtn
        return rtn


    @staticmethod
    def merge(qsa, qsb):
        stocks = {}
        for each in qsa.stocks:
            stocks[each.symbol] = each
        for each in qsb.stocks:
            if each.symbol not in stocks:
                stocks[each.symbol] = each
        return QuerySet(stocks.values())


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
        print all.run_script('filter(":instant::high","$gte",":instant::high52week").orderby(":instant::symbol")')
        
        

