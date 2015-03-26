#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys, time
from optparse import OptionParser
from api import XueqiuAPI, time_parse, current_tick
from pymongo import MongoClient
from datetime import datetime, timedelta
from core.ticker import TradeCalendar,RT
from common.utils import gen_time, standarlize_time, gen_tick

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
    def __init__(self, ip='127.0.0.1', port=27017, gentle=False):
        self.api = XueqiuAPI()
        self.db = MongoClient(ip, port).opentrader
        self.gentle = gentle

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
            if self.gentle:
                time.sleep(1)
        return updated

    def sync_xueqiu_k_day_pure(self, symbols=None, begin=None, end=None):
        print 'Start syncing k day pure...'
        # standarlize begin/end
        begin = standarlize_time(begin)
        end = standarlize_time(end)
        total_updated = 0
        assert symbols is not None

        for (i, sym) in enumerate(symbols):
            updated = 0
            ks = self.api.stock_k_day(sym, begin=begin, end=end)
            if not ks:
                print 'stock %d: %s... fetch failure' % (i, sym)
                continue
            real_latest_time = time_parse(ks[-1]['time'])
            for k in ks:
                k['time'] = time_parse(k['time'])
                entry = self.db.xueqiu_k_day.find_one({'symbol':sym, 'time':k['time']})
                k['symbol'] = sym
                if not entry:
                    self.db.xueqiu_k_day.insert(k)
                    total_updated += 1
                    updated += 1
            print 'stock %d: %s... inserted %d entries with latest time %s' % (i, sym, updated, str(real_latest_time))

    # {"symbol":"SH000001", "time":"Mon Jan 13 00:00:00 +0800 2014", "volume":1.019157E7,"open":14.82,"high":15.35,"close":14.9,"low":14.51,"chg":0.0,"percent":0.0,"turnrate":1.52,"ma5":15.05,"ma10":15.13,"ma20":15.1,"ma30":15.66,"dif":-0.56,"dea":-0.71,"macd":0.3}
    # notice to create index for mongodb: db.xueqiu_k_day.ensureIndex({symbol:1, time:1},{unique:true, dropDups:true})
    # begin, end: support both string or datetime
    def sync_xueqiu_k_day(self, symbols=None, begin=None, end=None, forcecal=False, forcefetch=False, skip=0):
        print 'Start syncing xueqiu k day...'
        # standarlize begin/end
        begin = standarlize_time(begin)
        end = standarlize_time(end)
        total_updated = 0
        if symbols is None:
            symbols = self.get_normal_symbols()
            #symbols = [info['symbol'] for info in self.db.xueqiu_info.find({'current':{'$ne':0}})]

        if end is None:
            latest_date = TradeCalendar.get_latest_date_before(date.today())
            latest_time = datetime(latest_date.year, latest_date.month, latest_date.day)
        else:
            latest_date = TradeCalendar.get_latest_date_before(end.date())
            latest_time = datetime(latest_date.year, latest_date.month, latest_date.day)

        for (i, sym) in enumerate(symbols):
            if i < skip:
                continue
            updated = 0
            stock_with_latest_time = self.db.xueqiu_k_day.find_one({'symbol': sym, 'time':latest_time})
            if stock_with_latest_time and not forcefetch:
                print 'stock %d: %s... already have it for latest date %s' % (i, sym, str(latest_time))
                # already has latest date for this symbol, no need to query it.
                if forcecal:
                    # fetch the entry_list from database
                    entry_list = list(self.db.xueqiu_k_day.find({'symbol':sym, 'time':{'$gte':begin, '$lte':end}}))
            else:
                entry_list = [] # for calculation work
                ks = self.api.stock_k_day(sym, begin=begin, end=end)
                if not ks:
                    print 'stock %d: %s... fetch failure' % (i, sym)
                    continue
                real_latest_time = time_parse(ks[-1]['time'])
                for k in ks:
                    k['time'] = time_parse(k['time'])
                    entry = self.db.xueqiu_k_day.find_one({'symbol':sym, 'time':k['time']})
                    k['symbol'] = sym
                    if not entry:
                        self.db.xueqiu_k_day.insert(k)
                        total_updated += 1
                        updated += 1
                        entry_list.append(k)
                    else:
                        entry_list.append(entry)
                print 'stock %d: %s... inserted %d entries with latest time %s' % (i, sym, updated, str(real_latest_time))

            #########################
            # make calculations
            #########################
            if forcecal or not stock_with_latest_time:
                high20_updated = 0
                high55_updated = 0
                atr20_updated = 0
                for j, entry in enumerate(entry_list):
                    # high 20
                    if j >= 19 and 'high20' not in entry:
                        high = 0
                        for k in range(j-19, j+1): # notice this range is from j-19 to j
                            if entry_list[k]['high'] > high:
                                high = entry_list[k]['high']
                        entry['high20'] = high
                        self.db.xueqiu_k_day.update({'symbol':entry['symbol'], 'time':entry['time']}, {'$set':{'high20':high}})
                        high20_updated += 1

                    # high 55
                    if j >= 54 and 'high55' not in entry:
                        high = 0
                        for k in range(j-54, j+1): # notice this range is from j-54 to j
                            if entry_list[k]['high'] > high:
                                high = entry_list[k]['high']
                        entry['high55'] = high
                        self.db.xueqiu_k_day.update({'symbol':entry['symbol'], 'time':entry['time']}, {'$set':{'high55':high}})
                        high55_updated += 1
                    
                    # atr 20
                    if j >= 19 and 'atr20' not in entry:
                        TRs = 0
                        for k in range(j-19, j+1):
                            if k == 0:
                                PDC = entry_list[k]['open']
                            else:
                                PDC = entry_list[k-1]['close']
                            H = entry_list[k]['high']
                            L = entry_list[k]['low']
                            TR = max(H-L, H-PDC, PDC-L)
                            TRs += TR
                        entry['atr20'] = round(float(TRs)/20.0, 2)
                        self.db.xueqiu_k_day.update({'symbol':entry['symbol'], 'time':entry['time']}, {'$set':{'atr20':entry['atr20']}})
                        atr20_updated += 1

                print 'stock %d: %s... %d high20 updated, %d high55 updated, %d atr20 updated' % (i, sym, high20_updated, high55_updated, atr20_updated)
                
            if self.gentle:
                time.sleep(1)
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
                instant_data = self.api.stock_instant(tmp_sym_list)
                if not instant_data:
                    print 'stock %d: %s... fail to query from xueqiu instant for today %s' % (i, tmp_sym_list, str(today))
                    continue
		# only remove the old one when the new data is successfully fetched
                self.db.xueqiu_instant.remove({'symbol':{'$in':tmp_sym_list}, 'date':today})
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
                if self.gentle:
                    time.sleep(0.5)
            else:
                tmp_sym_list.append(sym)
        return updated

# XXX mostly for temperary usage.
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
        end = datetime.now()
        begin = end - timedelta(days=1) # one day ago
        #sync_xueqiu_k_day_pure(symbols=['SH000001'], begin=begin, end=end)
        #syncer.sync_xueqiu_k_day(symbols=stocks, begin=begin, end=end)
    # -a
    elif options.all is not None:
        syncer = XueqiuSyncer()
        #syncer.sync_xueqiu_k_day(symbols=stocks)
        syncer.sync_xueqiu_k_day(symbols=stocks, begin='2014-01-01 00:00:00', end='2015-03-16 16:16:16', forcefetch=True, forcecal=True, skip=0)
    # -i - should be run after 9:30 a.m., before 12:00 p.m. of every trading day.
    elif options.instant is not None:
        syncer = XueqiuSyncer()
        #syncer.sync_xueqiu_price(symbols=stocks)
        syncer.sync_xueqiu_instant(symbols=stocks)
        end = datetime.now()
        begin = end - timedelta(days=1) # one day ago
        #syncer.sync_xueqiu_k_day(symbols=stocks, begin=begin, end=end)
    else:
        pass
    RT.stop()



if __name__ == "__main__":
    main()

def test_xueqiu_k_day():
    syncer = XueqiuSyncer()
    syncer.db.xueqiu_k_day.remove({'symbol':'SZ000025'})
    syncer.sync_xueqiu_k_day(symbols=['SZ000025'], begin='2012-01-01 00:00:00', end='2015-03-04 00:00:00')
    assert syncer.db.xueqiu_k_day.find({'symbol':'SZ000025', 'time':gen_time("2015-03-02 00:00:00")})[0]['high20'] == 15.8
    assert syncer.db.xueqiu_k_day.find({'symbol':'SZ000025', 'time':gen_time("2015-03-04 00:00:00")})[0]['high20'] == 16.18
    assert syncer.db.xueqiu_k_day.find({'symbol':'SZ000025', 'time':gen_time("2015-02-27 00:00:00")})[0]['high20'] == 14.76
    syncer.sync_xueqiu_k_day(symbols=['SZ000025'], begin='2012-01-01 00:00:00', end='2015-03-05 00:00:00')
    assert syncer.db.xueqiu_k_day.find({'symbol':'SZ000025', 'time':gen_time("2015-03-05 00:00:00")})[0]['high20'] == 16.18
    assert syncer.db.xueqiu_k_day.find({'symbol':'SZ000025', 'time':gen_time("2015-03-05 00:00:00")})[0]['atr20'] == 0.74
    RT.stop()

