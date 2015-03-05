#!/usr/bin/python
import os, sys
from optparse import OptionParser
from sync import XueqiuSyncer
from api import XueqiuAPI, time_parse, current_tick
from datetime import datetime,date
import time
from core.query import QuerySet
from common.db import db_ot
import pymongo
from core.ticker import TradeCalendar
from common.utils import gen_time

# db.policy_newhigh_52w.ensureIndex({date:1, time:1})

def convert_newhigh_policy():
    entries = list(db_ot.policy_newhigh.find().sort('time', 1))
    date_dict = {}
    for entry in entries:
        if entry['date'] not in date_dict:
            date_dict[entry['date']] = []
        for symbol in entry['symbols']:
            if symbol not in date_dict[entry['date']]:
                date_dict[entry['date']].append(symbol)
                # insert into the new collection
                print entry['time'], entry['date'], symbol
                db_ot.policy_newhigh_52w.insert({'time':entry['time'], 'date':entry['date'], 'symbol':symbol})

def check_repeat_newhigh_52w(symbol, today=None):
    if today is None:
        today = date.today()
    oldday = TradeCalendar.get_date(today, -10)
    if oldday is None:
        print 'invalid date'
        return False # not repeat
    oldday_datetime = datetime(oldday.year, oldday.month, oldday.day)
    today_datetime = datetime(today.year, today.month, today.day)
    result = db_ot.policy_newhigh_52w.find_one({'date':{'$gte':oldday_datetime, '$lt':today_datetime}, 'symbol':symbol})
    if not result:
        return False
    else:
        return True


def update_newhigh_52w():
    now = datetime.now()
    today_datetime = datetime(now.year, now.month, now.day)
    q = QuerySet.all().run_script('filter(":instant::high","$gte",":instant::high52week").orderby(":instant::symbol")')
    sym_list = [s.symbol for s in q.stocks]

    existing_dict = {}
    existing = list(db_ot.policy_newhigh_52w.find({'date':today_datetime}))
    for each in existing:
        existing_dict[each['symbol']] = each

    result_exist_list = []
    result_new_list = []
    result_repeat_list = []
    for symbol in sym_list:
        if symbol in existing_dict:
            result_exist_list.append(symbol)
            continue # already exists
        else:
            if check_repeat_newhigh_52w(symbol):
                result_repeat_list.append(symbol)
                db_ot.policy_newhigh_52w.insert({'date':today_datetime, 'time':now, 'symbol':symbol, 'new':0})
            else:
                result_new_list.append(symbol)
                db_ot.policy_newhigh_52w.insert({'date':today_datetime, 'time':now, 'symbol':symbol, 'new':1})
    print "Updated newhigh 52w: existing %d %s, new %d %s, repeat %d %s." % (len(result_exist_list), str(result_exist_list), len(result_new_list), str(result_new_list), len(result_repeat_list), str(result_repeat_list))

def get_newhigh_52w(today=None):
    if today is None:
        today = date.today()
    brand_new_list = []
    repeat_list = []
    today_datetime = datetime(today.year, today.month, today.day)
    records = list(db_ot.policy_newhigh_52w.find({'date':today_datetime}).sort('time', pymongo.DESCENDING))
    for record in records:
        if check_repeat_newhigh_52w(record['symbol'], today):
            repeat_list.append(record)
        else:
            brand_new_list.append(record)
    return (brand_new_list, repeat_list)

def test_get_newhigh_52w():
    test_date = gen_time('2015-03-02 00:00:00').date()
    assert len(get_newhigh_52w(test_date)[0]) == 74
    assert len(get_newhigh_52w(test_date)[1]) == 244

