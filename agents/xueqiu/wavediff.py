import sys, os
sys.path.append("../../")
from api import XueqiuAPI, time_parse
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import matplotlib.font_manager as font_manager
import json

if os.path.exists('wavediff.json'):
    f = open('wavediff.json', 'r')
    read_data = f.read()
    obj = json.loads(read_data)
    sz50 = obj['sz50']
    hs300 = obj['hs300']
    zz500 = obj['zz500']
    cyb = obj['cyb']
    f.close()
else:
    api = XueqiuAPI()
    sz50 = api.stock_k_day(symbol="SH000016", begin="2015-02-01 00:00:00", end="2015-08-03 00:00:00")
    hs300 = api.stock_k_day(symbol="SH000300", begin="2015-02-01 00:00:00", end="2015-08-03 00:00:00")
    zz500 = api.stock_k_day(symbol="SH000905", begin="2015-02-01 00:00:00", end="2015-08-03 00:00:00")
    cyb = api.stock_k_day(symbol="SZ399006", begin="2015-02-01 00:00:00", end="2015-08-03 00:00:00")
    f = open('wavediff.json', 'w')
    obj = {'sz50':sz50, 'hs300':hs300, 'zz500':zz500, 'cyb':cyb}
    f.write(json.dumps(obj))
    f.close()

#sz50 = api.stock_k_day('SZ', '000016', '20150401', '20150803')['hq']
#hs300 = api.stock_k_day('SZ', '000300', '20150401', '20150803')['hq']
#zz500 = api.stock_k_day('SZ', '000905', '20150401', '20150803')['hq']
#cyb = api.stock_k_day('SZ', '399006', '20150401', '20150803')['hq']

rate_avr = []
for i in range(len(sz50)):
    val = 0
    for target in (sz50, hs300, zz500, cyb):
        val += float(target[i]["percent"])
    val /= 4
    rate_avr.append(val)
print("length is %d" % len(rate_avr))

def compute_earning():
    owning = {"sz50":0, "hs300":0, "zz500":0, "cyb":0}
    cur_earn = 0
    earning = 0
    earning_list = []
    cur_long_sym = None
    cur_short_sym = None
    cur_long2_sym = None
    cur_short2_sym = None
    for i in range(len(sz50)):
        sym_dict = {}
        sym_dict[str(sz50[i]['percent'])] = 'sz50'
        sym_dict[str(hs300[i]['percent'])] = 'hs300'
        sym_dict[str(zz500[i]['percent'])] = 'zz500'
        sym_dict[str(cyb[i]['percent'])] = 'cyb'
        percents = [sz50[i]['percent'], hs300[i]['percent'], zz500[i]['percent'], cyb[i]['percent']]
        percents.sort()
        percents.reverse()
        max_val = percents[0]
        max_sym = sym_dict[str(max_val)]
        min_val = percents[3]
        min_sym = sym_dict[str(min_val)]
        cur_earn = owning['sz50']*sz50[i]['percent']+owning['hs300']*hs300[i]['percent']+owning['zz500']*zz500[i]['percent']+owning['cyb']*cyb[i]['percent']
        earning += cur_earn
        if max_val - min_val >= 0.3:
            if cur_short_sym:
                owning[cur_short_sym] += 1
            if cur_long_sym:
                owning[cur_long_sym] -= 1
            owning[min_sym] -= 1
            owning[max_sym] += 1
            cur_short_sym = min_sym
            cur_long_sym = max_sym

            #if cur_short2_sym:
            #    owning[cur_short2_sym] += 1
            #if cur_long2_sym:
            #    owning[cur_long2_sym] -= 1
            #owning[sym_dict[str(percents[1])]] += 1
            #owning[sym_dict[str(percents[2])]] -= 1
            #cur_short2_sym = sym_dict[str(percents[2])]
            #cur_long2_sym = sym_dict[str(percents[1])]

        earning_list.append(earning)
        print("owning: %d,%d,%d,%d; perc: %.2f,%.2f,%.2f,%.2f; cur_earn: %f; earning: %f" % (owning['sz50'],owning['hs300'],owning['zz500'],owning['cyb'],sz50[i]['percent'],hs300[i]['percent'],zz500[i]['percent'],cyb[i]['percent'],cur_earn,earning))

    fig, ax = plt.subplots()
    ax.plot(earning_list)
    ax.grid(True)
    plt.show()


years    = mdates.YearLocator()   # every year
months   = mdates.MonthLocator()  # every month
yearsFmt = mdates.AutoDateFormatter(months)

def plot_avr_bias():
    fig, ax = plt.subplots()

    for src_data in (sz50, hs300, zz500, cyb):
        print(11)
        print(len(src_data))
        src_data_copy = []
        for i in range(len(src_data)):
            each = src_data[i]
            new = [None]*5
            new[0] = time_parse(each["time"]).strftime("%Y-%m-%d")
            new[1] = float(each["open"])
            new[2] = float(each["close"])
            new[3] = float(each["chg"])
            #try:
            new[4] = float(each["percent"]) - rate_avr[i]
            src_data_copy.append(tuple(new[:5]))

        data = np.array(src_data_copy, dtype=[('date', 'datetime64[D]'), ('open', float), ('close', float), ('change', float), ('rate', float)])
        r = data.view(np.recarray)
        print(r.date)
        print(r.rate)
        ax.plot(r.date, r.rate)

    #props = font_manager.FontProperties(size=10)
    #leg = ax.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
    #leg.get_frame().set_alpha(0.5)

    ## format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.grid(True)
    #fig.autofmt_xdate()
    plt.show()


def plot_basis_bias():
    fig, ax = plt.subplots()

    src = 0
    for src_data in (sz50, hs300, zz500, cyb):
        src_data_copy = []
        base = float(src_data[0][2])
        for i in range(len(src_data)):
            each = src_data[i]
            each[0] = str(each[0])
            each[1] = float(each[1])
            each[2] = float(each[2]) / base - 1.0
            each[3] = float(each[3])
            try:
                each[4] = float(each[4][:-1])
            except IndexError:
                continue
            src_data_copy.append(tuple(each[:5]))

        data = np.array(src_data_copy, dtype=[('date', 'datetime64[D]'), ('open', float), ('close', float), ('change', float), ('rate', float)])
        r = data.view(np.recarray)
        ax.plot(r.date, r.close, label=("sz50", "hs300", "zz500", "cyb")[src])
        src += 1
        print(r.rate)

    fig.autofmt_xdate()

    props = font_manager.FontProperties(size=10)
    leg = ax.legend(loc='upper left', shadow=True, fancybox=True, prop=props)
    leg.get_frame().set_alpha(0.5)

    ## format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.grid(True)
    fig.autofmt_xdate()
    plt.show()

#plot_basis_bias()
compute_earning()
#plot_avr_bias()

