#!/usr/bin/python
# -*- coding: utf-8 -*-
from common.db import db_ot
import pymongo
from datetime import datetime

class StockDataNotExist(Exception):
    pass

# stock main class
class Stock(object): 
    def __init__(self, symbol=None, info=None, instant=None, initialized=False):
        self.symbol = symbol
        if info is None:
            self._info = db_ot.xueqiu_info.find_one({'symbol':self.symbol})
        else:
            self._info = info

        today = datetime.today()
        today = datetime(today.year, today.month, today.day)
        if instant is None and initialized == False:
            self._latest_instant = db_ot.xueqiu_instant.find_one({'symbol':self.symbol, 'date':today})
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
        s = Stock('SZ002736')
        assert s is not None
        assert s.name == u'国信证券'
        
        
        