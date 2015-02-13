#!/usr/bin/python
import os, sys
from optparse import OptionParser
from sync import XueqiuSyncer
from datetime import datetime
import time
from core.query import QuerySet
from common.db import db_ot
import pymongo

def sync_inst():
    syncer = XueqiuSyncer()
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    print now
    try:
        syncer.sync_xueqiu_instant()
    except:
        print 'error syncing xueqiu instant'
    #####################
    # Policy New High
    #####################
    q = QuerySet.all().run_script('filter(":instant::high","$gte",":instant::high52week").orderby(":instant::symbol")')
    sym_list = [s.symbol for s in q.stocks]
    existing = list(db_ot.policy_newhigh.find({'date':today}).sort('time', pymongo.DESCENDING))
    if existing:
        print 'existing new high: %s' % existing[0]
    # compare sym_list with the existing list
    if existing and existing[0]['symbols'] == sym_list:
        pass
    else:
        db_ot.policy_newhigh.insert({'date':today, 'time':now, 'symbols':sym_list})
        print 'newhigh symbol list inserted: %s' % sym_list

def sync_list():
    syncer = XueqiuSyncer()
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    print now
    try:
        syncer.sync_xueqiu_info()
    except:
        print 'error syncing xueqiu info'
            
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

if __name__ == "__main__":
    main()
