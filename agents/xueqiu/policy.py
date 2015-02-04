#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys, csv
from optparse import OptionParser
from api import XueqiuAPI, time_parse, current_tick
from pymongo import MongoClient
from datetime import datetime, timedelta
from sync import XueqiuSyncer

def gen_time(str_time):
    return datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")

def check_matching_stocks(date=None, yesterday=None):
    db = MongoClient('127.0.0.1', 27017).opentrader
    date = gen_time(date)
    yesterday = gen_time(yesterday)
    greater_than_7 = db.xueqiu_k_day.find({'time':date, 'percent':{'$gt':7}})
    to_rtn = []
    for each_stock in greater_than_7:
        # find yesterday's data
        print each_stock['symbol']
        yest = db.xueqiu_k_day.find_one({'symbol':each_stock['symbol'], 'time':yesterday})
        if not yest:
            print 'no yesterday data'
            continue
        print each_stock['volume'] / yest['volume']
        if (each_stock['volume'] / yest['volume']) <= 1.3:
            each_stock['volume_change'] = each_stock['volume'] / yest['volume']
            info = db.xueqiu_info.find_one({'symbol':each_stock['symbol']})
            if not info:
                continue
            each_stock['name'] = info['name'].encode('utf-8')
            to_rtn.append(each_stock)
    sorted_list1 = sorted(to_rtn, key=lambda k: k['percent'])
    sorted_list2 = sorted(to_rtn, key=lambda k: k['volume_change'])
    
    with open('1.csv', 'wb') as csvfile:
        fieldnames = sorted_list1[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for each in sorted_list1:
            try:
                writer.writerow(each)
            except ValueError:
                print each

    with open('2.csv', 'wb') as csvfile:
        fieldnames = sorted_list2[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for each in sorted_list2:
            writer.writerow(each)


    return (sorted_list1, sorted_list2)

"""
def over_night_regression(date=None):
    db = MongoClient('127.0.0.1', 27017).opentrader
    date = gen_time(date)
    for each_stock in db.xueqiu_price.find({'date':date}):
        k_data = db.xueqiu_k_day.find({'date':date, 'symbol':each_stock['symbol']})
        if not k_data:
            continue
        instant_data = db.xueqiu_instant.find
        if each_stock['prices'][-8]['current']
"""

def over_night_today():
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)
    yesterday = today - timedelta(1)
    db = MongoClient('127.0.0.1', 27017).opentrader
    syncer = XueqiuSyncer()
    # now sync the instant data
    syncer.sync_xueqiu_info()
    api = XueqiuAPI()
    to_rtn = []
    greater_than_7 = db.xueqiu_info.find({'percent':{'$gt':7}})
    sys.stdout.write('\nHandling %d stocks with percent over 7' % greater_than_7.count())
    sys.stdout.flush()
    for each_stock in greater_than_7:
        sys.stdout.write('.')
        sys.stdout.flush()
        instant_data = api.stock_instant([each_stock['symbol']])[0]
        if not instant_data:
            continue
        yesterday_k = db.xueqiu_k_day.find_one({'symbol':each_stock['symbol'], 'time':yesterday})
        if not yesterday_k:
            continue
        volume_change = float(instant_data['volume']) / yesterday_k['volume']
        if volume_change > 1.3:
            continue
        if float(instant_data['high']) == float(instant_data['current']) or float(instant_data['high']) < float(instant_data['rise_stop']):
            stock_rtn = {
                'symbol': each_stock['symbol'],
                'name': each_stock['name'].encode('utf-8'),
                'current': float(instant_data['current']),
                'percent': float(instant_data['percentage']),
                'is_highest': instant_data['current'] == instant_data['high'],
                'is_stopped': instant_data['high'] == instant_data['rise_stop'],
                'volume_change': volume_change
            }
            to_rtn.append(stock_rtn)
        else:
            pass

    sorted_list = sorted(to_rtn, key=lambda k: k['percent'], reverse=True)
    with open('3.csv', 'wb') as csvfile:
        fieldnames = sorted_list[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for each in sorted_list:
            writer.writerow(each)

    return to_rtn





#print check_matching_stocks('2015-01-12 00:00:00', '2015-01-09 00:00:00')
#print over_night_today()
