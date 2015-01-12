#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
from optparse import OptionParser
from api import XueqiuAPI, time_parse
from pymongo import MongoClient
from datetime import datetime

# convert in-place
def convert_str_to_number(doc, int_keys=[], float_keys=[]):
    try:
        for key in int_keys:
            if doc[key].strip() == '':
                doc[key] = 0
                continue
            doc[key] = int(doc[key])
        for key in float_keys:
            if doc[key].strip() == '':
                doc[key] = 0
                continue
            doc[key] = float(doc[key])
    except KeyError:
        pass
            

class XueqiuSyncer(object):
    def __init__(self, ip='127.0.0.1', port=27017):
        self.api = XueqiuAPI()
        self.db = MongoClient(ip, port).opentrader

    # {"symbol":"SZ002738","code":"002738","name":"中矿资源",
    #  "current":"19.32","percent":"10.02","change":"1.76","high":"19.32","low":"19.32",
    #  "high52w":"19.32","low52w":"9.08","marketcapital":"2.3184E9","amount":"7246932.0",
    #  "pettm":"79.63","volume":"375100","hasexist":"false"}
    def sync_xueqiu_info(self, symbols=None):
        # get the stock info from api
        info_list = self.api.stock_list()
        to_insert = []
        for each_info in info_list:
            if symbols is not None and each_info['symbol'] not in symbols:
                continue
            convert_str_to_number(each_info, ['volume'], 
                                  ['current', 'percent', 'change', 
                                   'high', 'low', 'high52w', 'low52w',
                                   'marketcapital', 'amount', 'pettm'])
            each_info['synctime'] = datetime.now()
            to_insert.append(each_info)
        self.db.xueqiu_info.remove()
        self.db.xueqiu_info.insert(to_insert)

    def _get_normal_symbols():
        pass

    # sync price curve of one day (today) to database
    # {"symbol":"SH000001", "prices":[{"volume":227700.0,"current":33.35,"time":"Fri Jan 09 09:30:00 +0800 2015"},...]}
    def sync_xueqiu_price(self, symbols=None):
        updated = 0
        if symbols is None:
            symbols = [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}})]

        for sym in symbols:
            prices = self.api.stock_price(sym)
            for each in prices:
                each['time'] = time_parse(each['time'])
            # find whether there is this stock for this date
            date = prices[0]['time'].date()
            date = datetime(date.year, date.month, date.day)
            stock = self.db.xueqiu_price.find_one({'symbol': sym, 'date': date})
            if not stock:
                self.db.xueqiu_price.insert({'symbol':sym, 'prices':prices, 'date':date})
                updated += 1
        return updated

    # {"symbol":"SH000001", "time":"Mon Jan 13 00:00:00 +0800 2014", "volume":1.019157E7,"open":14.82,"high":15.35,"close":14.9,"low":14.51,"chg":0.0,"percent":0.0,"turnrate":1.52,"ma5":15.05,"ma10":15.13,"ma20":15.1,"ma30":15.66,"dif":-0.56,"dea":-0.71,"macd":0.3}
    def sync_xueqiu_k_day(self, symbols=None, begin=None, end=None):
        updated = 0
        if symbols is None:
            symbols = [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}})]

        for sym in symbols:
            ks = self.api.stock_k_day(sym, begin=begin, end=end)
            if not ks:
                continue
            for k in ks:
                k['time'] = time_parse(k['time'])
                entry = self.db.xueqiu_k_day.find_one({'symbol':sym, 'time':k['time']})
                k['symbol'] = sym
                if not entry:
                    self.db.xueqiu_k_day.insert(k)
                    updated += 1
        return updated









def main():
    USAGE = """
    usage: python sync.py -l (sync basic info of a complete stock list)
           python sync.py -a [-s SZ002738,SH000001] (sync all from xueqiu - except the stock list)
           python sync.py -i [-s SZ002738,SH000001] (sync instant data by now - usually to update today or the last trading day)
    """
    
    if len(sys.argv) < 2:
        print USAGE
        exit(1)

    sys_args = sys.argv[1:]

    parser = OptionParser(USAGE)
    parser.add_option('-l', '--list', action="store_false")
    parser.add_option('-a', '--all', action="store_false")
    parser.add_option('-i', '--instant', action="store_false")
    parser.add_option('-s', '--stock')
    (options, args) = parser.parse_args(sys_args)
    if options.stock is not None:
        stocks = options.stock.split(',')
    else:
        stocks = None
    # -l
    if options.list is not None:
        syncer = XueqiuSyncer()
        syncer.sync_xueqiu_info()
    # -a
    elif options.all is not None:
        syncer = XueqiuSyncer()
        syncer.sync_xueqiu_price(symbols=stocks)
        syncer.sync_xueqiu_k_day(symbols=stocks)

    elif options.instant is not None:
        pass
    else:
        pass



if __name__ == "__main__":
    main()
