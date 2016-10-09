import sys
# coding: utf-8

# In[1]:

# 本脚本用于每日实盘操作及理论值的对比，整个脚本的运行有两种模式：
#real模式用于收盘前的实盘操作
#close模式用于收盘后的检验
mode = sys.argv[1]
if not mode:
    mode = "real"
print(mode)
from opentrader.core.crawler import *
from opentrader.agents.xueqiu.api import *
from opentrader.agents.ths.api import *

c = CNCrawler()
stock_list = c.get_stock_list()
stock_percent = {}
for each in stock_list:
    stock_percent[each['symbol']] = float(each['percent'])


# In[2]:

# Use multiple threads to query iwencai flags and symbols
from opentrader.common.db import db_ot
from opentrader.common.utils import d2dt
from pymongo.errors import *
import threading,json,sys
from datetime import date
flagf = open("iwencai_flags.json", "r")
allflags = json.loads(flagf.read())
lock_allflags = threading.RLock()
flagf.close()

flag_symbols = {} # {"...flag...":[<symbol1>, <symbol2>, ...], ...}
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
        
f = open("./flag_symbols_"+mode+"_"+str(date.today())+".json", "w")
f.write(json.dumps(flag_symbols))
f.close()


# In[3]:

# Turn {flag:[symbols]} into {symbol:[flags]}
symbol_flags = {}
for (flag, symbols) in flag_symbols.items():
    for each in symbols:
        if each not in symbol_flags:
            symbol_flags[each] = []
        symbol_flags[each].append(flag)
print("total flags: %d, total symbols: %d" % (len(flag_symbols), len(symbol_flags)))


# In[6]:

# check today's stocks with most buy flags
import operator, datetime
from datetime import datetime,timedelta
from opentrader.common.db import db_ot

f = open('iwencai_flag_performance_onedayf_all.json', 'r')
flagperformance = json.loads(f.read())
f.close()

stockmeans = {}
stock_maxflag = {}
totalflags = 0
totalmean = 0

for (symbol, flags) in symbol_flags.items():
    symbol = symbol_convert3(symbol)
    stockmean = 0
    stock_flag_count = 0
    maxflag = ['', 0]
    filter_symbol = False
    for flag in flags:
        if flag in ('停牌','涨停'):# 此处过滤 “涨停” 是为了滤掉ST股票的影响
            filter_symbol = True
        if flag not in flagperformance:
            continue
        stock_flag_count += 1
        stockmean += flagperformance[flag]['avr']
        totalflags += 1
        totalmean += flagperformance[flag]['avr']
        if flagperformance[flag]['avr'] > maxflag[1]:
            maxflag[1] = flagperformance[flag]['avr']
            maxflag[0] = flag
    if stock_flag_count == 0:
        continue
    stockmean = stockmean / stock_flag_count
    if stock_percent[symbol] > 9.8 or filter_symbol:
        continue
    stockmeans[symbol] = stockmean
    stock_maxflag[symbol] = maxflag
            
sorted_x = sorted(stockmeans.items(), key=operator.itemgetter(1))
sorted_x.reverse()
print(totalmean/totalflags)
print(len(sorted_x))

outdata = {"mode":mode, "index":totalmean/totalflags, "data":[], "time":datetime.now()}
for each in sorted_x[:100]:
    outdata['data'].append({"symbol":each[0], "mean":each[1], "max_flag":stock_maxflag[each[0]][0], "max_flag_mean":stock_maxflag[each[0]][1]})
    print("symbol: %s, mean: %f, max flag: %s, max flag mean: %f" % (each[0], each[1], stock_maxflag[each[0]][0], stock_maxflag[each[0]][1]))
#f = open("./output_"+mode+"_"+str(date.today())+".json", "w")
#f.write(json.dumps(outdata))
#f.close()
db_ot.str_419.insert(outdata)


# 
