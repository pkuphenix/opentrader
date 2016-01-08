from opentrader.agents.ths.api import *
from opentrader.common.db import db_ot
from opentrader.common.utils import d2dt
from pymongo.errors import *
import threading,json,sys
from datetime import date
flagf = open("../../jupyter/crawler/iwencai_flags.json", "r")
allflags = json.loads(flagf.read())
lock_allflags = threading.RLock()
flagf.close()

flag_symbols = {}
lock = threading.RLock()

class FlagCrawler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.ths = THSAPI()

    def run(self):
        sys.stdout.write('b')
        sys.stdout.flush()
        i = 0
        while True:
            lock_allflags.acquire()
            try:
                flag = allflags.pop()
            except IndexError:
                lock_allflags.release()
                break
            lock_allflags.release()
            # search each flag at iwencai
            result = self.ths.query_iwencai(date.today().strftime('%Y年%m月%d日')+flag)
            try:
                result = result['result']
            except TypeError as e:
                sys.stdout.write(str(e))
            i += 1
            if i%2 == 0:
                sys.stdout.write(".")
            lock.acquire()
            flag_symbols[flag] = [each[0] for each in result]
            lock.release()
            sys.stdout.flush()
        sys.stdout.write('e%d' % (i))
        sys.stdout.flush()

threads = []
for i in range(20):
    thread = FlagCrawler()
    threads.append(thread)
    thread.start()

for each in threads:
    each.join()
        
f = open("../../jupyter/crawler/flag_symbols"+str(date.today())+".json", "w")
f.write(json.dumps(flag_symbols))
f.close()

    
