#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys
from optparse import OptionParser
from api import XueqiuAPI, time_parse, current_tick
from pymongo import MongoClient
from datetime import datetime

# convert in-place
def convert_str_to_number(doc, int_keys=[], float_keys=[]):
    try:
        for key in int_keys:
            if doc[key].strip() == '':
                doc[key] = 0
                continue
            try:
                doc[key] = int(doc[key])
            except ValueError:
                doc[key] = int(float(doc[key]))
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

    def get_normal_symbols(self):
        return [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}}) if not (info['symbol'].startswith("SH000") or info['symbol'].startswith("SH900") or info['symbol'].startswith("PRE") or info['symbol'].startswith("SZ399"))]

    # sync price curve of one day (today) to database
    # {"symbol":"SH000001", "prices":[{"volume":227700.0,"current":33.35,"time":"Fri Jan 09 09:30:00 +0800 2015"},...]}
    def sync_xueqiu_price(self, symbols=None):
        print 'Start syncing xueqiu price...'
        updated = 0
        if symbols is None:
            symbols = [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}})]

        for (i, sym) in enumerate(symbols):
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
                print 'stock %d: %s... inserted date %s' % (i, sym, str(date))
            else:
                print 'stock %d: %s... already have it for date %s' % (i, sym, str(date))
        return updated

    # {"symbol":"SH000001", "time":"Mon Jan 13 00:00:00 +0800 2014", "volume":1.019157E7,"open":14.82,"high":15.35,"close":14.9,"low":14.51,"chg":0.0,"percent":0.0,"turnrate":1.52,"ma5":15.05,"ma10":15.13,"ma20":15.1,"ma30":15.66,"dif":-0.56,"dea":-0.71,"macd":0.3}
    # notice to create index for mongodb: db.xueqiu_k_day.ensureIndex({symbol:1, time:1},{unique:true, dropDups:true})
    def sync_xueqiu_k_day(self, symbols=None, begin=None, end=None):
        print 'Start syncing xueqiu k day...'
        total_updated = 0
        if symbols is None:
            symbols = self.get_normal_symbols()
            #symbols = [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}})]

        latest_time = None
        for (i, sym) in enumerate(symbols):
            updated = 0
            if latest_time is not None:
                stock_with_latest_time = self.db.xueqiu_k_day.find_one({'symbol': sym, 'time':latest_time})
                if stock_with_latest_time:
                    print 'stock %d: %s... already have it for latest date %s' % (i, sym, str(latest_time))
                    continue # already has latest date for this symbol, no need to query it.
            
            ks = self.api.stock_k_day(sym, begin=begin, end=end)
            if not ks:
                print 'stock %d: %s... fetch failure' % (i, sym)
                continue
            latest_time = time_parse(ks[-1]['time'])
            for k in ks:
                k['time'] = time_parse(k['time'])
                entry = self.db.xueqiu_k_day.find_one({'symbol':sym, 'time':k['time']})
                k['symbol'] = sym
                if not entry:
                    self.db.xueqiu_k_day.insert(k)
                    total_updated += 1
                    updated += 1
            print 'stock %d: %s... inserted %d entries with latest time %s' % (i, sym, updated, str(latest_time))
        return total_updated
    """
    {"symbol":"SZ300059","exchange":"SZ","code":"300059","name":"东方财富","current":"41.25","percentage":"-5.56","change":"-2.430","open":"43.0","high":"44.0","low":"40.28","close":"0.0",
     "last_close":"43.68","high52week":"47.47","low52week":"8.99","volume":"4.2804822E7","volumeAverage":"46784325","marketCapital":"4.9896E10","eps":"0.05","pe_ttm":"550.7216","pe_lyr":"9983.7302",
     "beta":"0.0","totalShares":"1209600000","time":"Fri Feb 06 15:09:55 +0800 2015","afterHours":"0.0","afterHoursPct":"0.0","afterHoursChg":"0.0","afterHoursTime":"null","updateAt":"1423224015400",
     "dividend":"0.02","yield":"0.05","turnover_rate":"4.67","instOwn":"0.0","rise_stop":"48.05","fall_stop":"39.31","currency_unit":"CNY","amount":"1.77892612509E9","net_assets":"1.4374","hasexist":"false",
     "type":"11","flag":"1","rest_day":"","kzz_stock_symbol":"","kzz_stock_name":"","kzz_stock_current":"0.0","kzz_convert_price":"0.0","kzz_covert_value":"0.0","kzz_cpr":"0.0","kzz_putback_price":"0.0",
     "kzz_convert_time":"","kzz_redempt_price":"0.0","kzz_straight_price":"0.0","kzz_stock_percent":"","pb":"28.7","benefit_before_tax":"0.0","benefit_after_tax":"0.0","convert_bond_ratio":"",
     "totalissuescale":"","outstandingamt":"","maturitydate":"","remain_year":"","convertrate":"","interestrtmemo":"","release_date":"","circulation":"0.0","par_value":"0.0","due_time":"0.0",
     "value_date":"","due_date":"","publisher":"","redeem_type":"","issue_type":"","bond_type":"","warrant":"","sale_rrg":"","rate":"","after_hour_vol":"0","float_shares":"916024192",
     "float_market_capital":"3.778599792E10","disnext_pay_date":"","convert_rate":"","psr":"113.8297"}
    """
    def sync_xueqiu_instant(self, symbols=None):
        print 'Start syncing xueqiu instant...'
        updated = 0
        today = datetime.today()
        today = datetime(today.year, today.month, today.day)
        if symbols is None:
            symbols = self.get_normal_symbols()
            #symbols = [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}})]

        tmp_sym_list = []
        total_len = len(symbols)
        for (i, sym) in enumerate(symbols):
            if len(tmp_sym_list) == 100 or i == total_len-1:
                self.db.xueqiu_instant.remove({'symbol':{'$in':tmp_sym_list}, 'date':today})
                instant_data = self.api.stock_instant(tmp_sym_list)
                if not instant_data:
                    print 'stock %d: %s... fail to query from xueqiu instant for today %s' % (i, tmp_sym_list, str(today))
                    continue
                for each in instant_data:
                    each['time'] = time_parse(each['time'])
                    each['date'] = today
                    convert_str_to_number(each, 
                    ["volume","volumeAverage","marketCapital","totalShares","amount",
                     "type","after_hour_vol","float_shares","float_market_capital",], 
                    ["beta","afterHours","afterHoursPct","afterHoursChg","dividend","yield","turnover_rate","instOwn","rise_stop","fall_stop","net_assets",
                     "kzz_stock_current","kzz_convert_price","kzz_covert_value","kzz_cpr","kzz_putback_price","kzz_redempt_price","kzz_straight_price",
                     "kzz_stock_percent","pb","benefit_before_tax","benefit_after_tax","convert_bond_ratio","circulation","par_value","due_time","psr",
                     "current","percentage","change","open","high","low","close","last_close","high52week","low52week","eps","pe_ttm","pe_lyr",])
                self.db.xueqiu_instant.insert(instant_data)
                updated += len(tmp_sym_list)
                print '%d stocks: %s... inserted for today %s' % (len(tmp_sym_list), tmp_sym_list[0], str(today))
                tmp_sym_list = []
            else:
                tmp_sym_list.append(sym)
        return updated

def main():
    USAGE = """
    usage: python sync.py -l (sync basic info of a complete stock list)
           python sync.py -a [-s SZ002738,SH000001] (sync all k data from xueqiu - except the stock list)
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
        #syncer.sync_xueqiu_k_day(symbols=stocks)
        syncer.sync_xueqiu_k_day(symbols=stocks, begin='2012-01-01 00:00:00', end='2015-02-17 16:16:16')
    # -i - should be run after 9:30 a.m., before 12:00 p.m. of every trading day.
    elif options.instant is not None:
        syncer = XueqiuSyncer()
        #syncer.sync_xueqiu_price(symbols=stocks)
        syncer.sync_xueqiu_instant(symbols=stocks)
        end = current_tick()
        begin = end - 1000 * 24 * 3600 # one day ago
        #syncer.sync_xueqiu_k_day(symbols=stocks, begin=begin, end=end)
    else:
        pass



if __name__ == "__main__":
    main()
