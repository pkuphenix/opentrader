#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
from optparse import OptionParser
from api import XueqiuAPI, time_parse, current_tick
from pymongo import MongoClient
from datetime import datetime

class I419(object):
    def __init__(self, ip='127.0.0.1', port=27017):
        self.api = XueqiuAPI()
        self.db = MongoClient(ip, port).opentrader

    def get_normal_symbols(self):
        return [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}}) if not info['symbol'].startswith("SH000")]

    def generate_training(self, each_stock_limit=10000, stock_limit=3000):
        symbols = self.get_normal_symbols()
        i = 0
        for sym in symbols if i < stock_limit:
            # try to get at most "each_stock_limit" valid dataset from this symbol
            dates = list(self.db.xueqiu_k_day.find({'symbol':sym}))
            print len(dates)


i419 = I419()
i419.generate_training()
            

    
    
