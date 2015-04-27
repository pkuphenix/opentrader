#!/usr/bin/python
import os, sys
from optparse import OptionParser
from sync import XueqiuSyncer
from api import XueqiuAPI, time_parse, current_tick
from datetime import datetime, timedelta
import time
from core.query import QuerySet
from core.ticker import RT
from common.db import db_ot
import pymongo
from agents.xueqiu.newhigh import update_newhigh_52w

def sync_inst():
    syncer = XueqiuSyncer()
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    print now
    try:
        syncer.sync_xueqiu_instant()
    except:
        print 'error syncing xueqiu instant'
        raise
    #####################
    # Policy New High
    #####################
    try:
        update_newhigh_52w()
    except:
        print 'error updating 52week new high'
        raise
    #q = QuerySet.all().run_script('filter(":instant::high","$gte",":instant::high52week").orderby(":instant::symbol")')
    #sym_list = [s.symbol for s in q.stocks]
    #existing = list(db_ot.policy_newhigh.find({'date':today}).sort('time', pymongo.DESCENDING))
    #if existing:
    #    print 'existing new high: %s' % existing[0]
    # compare sym_list with the existing list
    #if existing and existing[0]['symbols'] == sym_list:
    #    pass
    #else:
    #    db_ot.policy_newhigh.insert({'date':today, 'time':now, 'symbols':sym_list})
    #    print 'newhigh symbol list inserted: %s' % sym_list

def sync_list():
    syncer = XueqiuSyncer(gentle=False)
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    end = datetime.now()
    begin = end - timedelta(days=10) # one day ago
    print now
    try:
        pass
        #syncer.sync_xueqiu_info()
    except:
        print 'error syncing xueqiu info'
        raise

    try:
        syncer.sync_xueqiu_k_day_pure(symbols=['SH000001'], begin='2012-12-01 00:00:00', end=end)
        #syncer.sync_xueqiu_k_day(begin=begin, end=end) # this won't calculate anything
        syncer.sync_xueqiu_k_day(begin='2015-01-01 00:00:00', end=end, forcecal=True)
    except:
        print 'error syncing xueqiu k day from %s to %s' % (str(begin), str(end))
        raise
            
def main():
    sys_args = sys.argv[1:]
    USAGE = """
    usage: python syncserver -i # run during trade time
           python syncserver -l # run after everyday close
    """
    parser = OptionParser(USAGE)
    parser.add_option('-i', action="store_true", dest="instant")
    parser.add_option('-l', action="store_true", dest="list")
    (options, args) = parser.parse_args(sys_args)
    if options.instant == True:
        sync_inst()
    if options.list == True:
        sync_list()
    RT.stop()

if __name__ == "__main__":
    main()
