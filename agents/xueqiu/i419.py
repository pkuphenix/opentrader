#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys, csv
from optparse import OptionParser
from api import XueqiuAPI, time_parse, current_tick
from pymongo import MongoClient
from datetime import datetime, timedelta
from prediction import *

def compute_delta_percent(dst, src, round_num=3):
    return round((dst/src-1)*100, round_num)

def gen_time(str_time):
    return datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")

class I419(object):
    def __init__(self, ip='127.0.0.1', port=27017):
        self.api = XueqiuAPI()
        self.db = MongoClient(ip, port).opentrader

    def get_normal_symbols(self):
        return [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}}) if not info['symbol'].startswith("SH000")]

    def generate_training(self, each_stock_limit=10000, stock_limit=3000):
        symbols = self.get_normal_symbols()
        i = 0
        result = []
        for sym in symbols:
            if i >= stock_limit:
                break
            j = 0
            # try to get at most "each_stock_limit" valid dataset from this symbol
            dates = list(self.db.xueqiu_k_day.find({'symbol':sym}))
            while j < len(dates)-5:
                if j >= each_stock_limit:
                    break
                # the initial base
                base = j
                # the initial target
                target = j+5
                src = base + 1
                data = []
                # target price
                data.append(compute_delta_percent(dates[target]['close'], dates[target-1]['close']))
                # src data
                while src < target:
                    data.append(compute_delta_percent(dates[src]['open'], dates[src-1]['close']))
                    data.append(compute_delta_percent(dates[src]['close'], dates[src-1]['close']))
                    data.append(compute_delta_percent(dates[src]['high'], dates[src-1]['close']))
                    data.append(compute_delta_percent(dates[src]['low'], dates[src-1]['close']))
                    data.append(compute_delta_percent(dates[src]['volume'], dates[src-1]['volume']))
                    data.append(dates[src]['turnrate'])
                    src += 1
                result.append(data)
                j += 1
            i += 1
            sys.stdout.write('.')
            sys.stdout.flush()
        with open('i419.csv', 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for each in result:
                writer.writerow(each)

    def evaluate(self, symbol=None, date=None):
        date = gen_time(date)
        assert symbol is not None
        dates = list(self.db.xueqiu_k_day.find({'symbol':symbol, 'time':{'$gte':date}}))
        data = []
        base = 0
        src = base + 1
        target = base + 5
        real_result = compute_delta_percent(dates[target]['close'], dates[target-1]['close'])
        while src < target:
            data.append(compute_delta_percent(dates[src]['open'], dates[src-1]['close']))
            data.append(compute_delta_percent(dates[src]['close'], dates[src-1]['close']))
            data.append(compute_delta_percent(dates[src]['high'], dates[src-1]['close']))
            data.append(compute_delta_percent(dates[src]['low'], dates[src-1]['close']))
            data.append(compute_delta_percent(dates[src]['volume'], dates[src-1]['volume']))
            data.append(dates[src]['turnrate'])
            src += 1
        pred = TrainedModel("154235034870", "i41901")
        print pred.predict(data)
        print (real_result, data)
        
        


i419 = I419()
#i419.generate_training(each_stock_limit=10, stock_limit=3000)
i419.evaluate("SZ300096", "2014-06-12 00:00:00")
            

