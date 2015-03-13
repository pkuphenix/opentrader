#!/usr/bin/python
# -*- coding: utf-8 -*-
from common.db import db_ot
import pymongo
from datetime import datetime
from core.ticker import Ticker, RT
from common.utils import gen_time

class StockDataNotExist(Exception):
    pass

# stock main class
class Stock(object): 
    def __init__(self, symbol=None, info=None, instant=None, initialized=False, ticker=None):
        self.symbol = symbol
        if info is None:
            self._info = db_ot.xueqiu_info.find_one({'symbol':self.symbol})
        else:
            self._info = info

        if ticker is None:
            self.ticker = RT
        else:
            self.ticker = ticker

        today = self.ticker.now.date()
        today = datetime(today.year, today.month, today.day)
        if instant is None and initialized == False:
            try:
                self._latest_instant = db_ot.xueqiu_instant.find({'symbol':self.symbol, 'date':{'$lte':today}}).sort('date', -1)[0]
            except IndexError:
                self._latest_instant = None
        else:
            self._latest_instant = instant
    
    def info(self, key=None, noexception=False):
        if self._info is None:
            if noexception:
                return None
            else:
                raise StockDataNotExist('info query error')

        if key is None:
            return self._info
        else:
            return self._info.get(key, None)

    def instant(self, key=None, noexception=False):
        if self._latest_instant is None:
            if noexception:
                return None
            else:
                raise StockDataNotExist('instant info query error')

        if key is None:
            return self._latest_instant
        else:
            return self._latest_instant.get(key, None)

    # returns (price, last_update_time)
    @property
    def latest_price(self):
        try:
            return (self.instant('current'), self.instant('time'))
        except StockDataNotExist:
            return (0, datetime.now())

    def atr(self, length):
        result = db_ot.xueqiu_k_day.find({'symbol':self.symbol}).sort('time', pymongo.DESCENDING).limit(length+1)
        result = list(result)
        result.reverse()
        if not result or len(result) < 2:
            raise StockDataNotExist('no enough data for ATR computing')
        i = 1
        TRs = 0
        while i < len(result):
            PDC = result[i-1]['close']
            H = result[i]['high']
            L = result[i]['low']
            TR = max(H-L, H-PDC, PDC-L)
            TRs += TR
            i += 1
        return round(float(TRs)/float(len(result)-1), 2)

    def kday(self, date):
        pass

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.symbol + '-' + self.name

    @property
    def name(self):
        return self.info('name')
    
class TestStock(object):
    def test_get_basic_info(self):
        s = Stock('SZ000559')
        assert s is not None
        assert s.name == u'万向钱潮'
        assert s.symbol == 'SZ000559'

    def test_get_instant_data(self):
        s = Stock('SZ000559')
        assert s.instant('current') == s.instant()['current']
        assert s.instant()['high'] >= s.instant()['low']
        assert s.instant('time') > datetime(2015, 2, 1)

        t = Ticker(begin=gen_time('2014-01-01 00:00:00'),
                   end=gen_time('2014-01-02 23:00:00'))
        s1 = Stock('SZ000559', ticker=t)
        def testrunner(e):
            print '%s: %s' % (e.name, str(e.source.now))
            print s1.instant('time')
        
        t.subscribe('ticker-begin', testrunner)

        
        
        
