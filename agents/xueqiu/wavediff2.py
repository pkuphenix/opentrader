#!/usr/bin/python
# -*- coding: utf-8 -*-
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

data_obj = {}
long_targets = [
    'SZ399807', # 高铁产业
    'SZ399975', # 证券公司
    'SH000971', # 等权90
    'SZ399970', # 移动互联
    'SZ399441', # 生物医药
    'SZ399990', # 煤炭等权
    'SZ399001', # 深证成指
    'SZ399007', # 深证300P
    'SZ399004', # 深证100R
    'SZ399330', # 深证100P
    'SZ399632', # 深100EW
    'SZ399300', # 沪深300
    'SZ399996', # 智能家居
    #'110000', # 恒生指数
    #'110010', # 恒生国企
    'SZ399803', # 工业4.0
    'SZ399550', # 央视50
    'SH000979', # 大宗商品
    'SH000966', # 基本400
    'SZ399983', # 地产等权
    'SZ399396', # 国证食品
    'SZ399440', # 国证钢铁
    'SZ399395', # 国证有色
    'SZ399412', # 国证新能
    'SZ399393', # 国证地产
    'SZ399394', # 国证医药
    'SZ399974', # 国企改革
    'SH000808', # 医药生物
    'SZ399006', # 创业板指
    'SZ399673', # 创业板50
    'SZ399958', # 创业成长
    'SZ399959', # 军工指数
    'SZ399944', # 内地资源
    'SZ399923', # 债券总指
    'SZ399994', # 信息安全
    'SZ399809', # 保险主题
    'SZ399805', # 互联金融
    'SH000833', # 中高企债
    'SZ399986', # 中证银行
    'SZ399934', # 中证金融
    'SZ399987', # 中证酒
    'SH000832', # 中证转债
    'SZ399997', # 中证白酒
    'SH000827', # 中证环保
    'SZ399998', # 中证煤炭
    'SZ399808', # 中证新能
    'SZ399973', # 中证国防
    'SZ399989', # 中证医疗
    'SZ399967', # 中证军工
    'SZ399481', # 中证全债
    'SZ399935', # 中证信息
    'SZ399804', # 中证体育
    'SZ399971', # 中证传媒
    'SH000998', # 中证TMT
    'SH000852', # 中证1000
    'SZ399903', # 中证100
    'SZ399905', # 中证 500
    'SZ399904', # 中证 200
    'SZ399005', # 中小板指
    'SZ399008', # 中小300P
    'SH000016', # 上证50
    'SZ399991', # 一带一路
    'SZ399610', # TMT50
    'SZ399976', # CS新能车
    'SZ399993', # CSWD生科
    'SZ399992', # CSWD并购
    'SZ399707', # CSSW证券
    'SZ399811', # CSSW电子
    'SZ399810', # CSSW传媒
    'SH000853', # CSSW丝路
    'SH000805', # A股资源
    'SH000974', # 800金融
    'SZ399966', # 800证保
    'SH000842', # 800等权
    'SH000823', # 800有色
    'SZ399965', # 800地产
    'SH000841', # 800医药
    'SZ399982', # 500等权
    'SH000828', # 500等权
    'SZ399918', # 300 成长
    'SH000010', # 上证180
    #'SH000905', # 中证500
    'SH000069', # 消费80
    'SH000021', # 180治理
    'SH000066', # 上证商品
    'SH000068', # 上证资源
    'SH000015', # 红利指数
    'SH000032', # 上证能源
    'SH000051', # 180等权
    'SH000009', # 上证380
    'SH000033', # 上证材料
    'SH000036', # 上证消费
    'SH000984', # 300等权
    'SH000018', # 180金融
    'SZ399634', # 中小板EW
    'SZ399324', # 深证红利
]
short_targets = [
    'SH000016', # sz50
    'SH000300', # hs300
    'SH000905', # zz500
    'SZ399006', # cyb
]
data_obj = {}
begin = "2011-01-01 00:00:00"
end="2015-10-13 00:00:00"
# obj containing data of every target:
# {"SH000016": [{"high": 2376.43, "ma5": 2437.67, "dea": 57.55, "chg": -72.85, "dif": 18.84, "time": "Mon Feb 02 00:00:00 +0800 2015", "percent": -3.03, "volume": 84676893.0, "macd": -77.42, "ma20": 2524.97, "low": 2329.15, "ma30": 2500.77, "close": 2332.53, "open": 2337.2, "ma10": 2480.56, "turnrate": 14.11},
if os.path.exists('wavediff.json'):
    f = open('wavediff.json', 'r')
    read_data = f.read()
    data_obj = json.loads(read_data)
    f.close()
else:
    api = XueqiuAPI()
    for symbol in long_targets+short_targets:
        print("fetching data of %s ..." % symbol)
        data = api.stock_k_day(symbol=symbol, begin=begin, end=end)
        data_obj[symbol] = data

    basis_length = len(data_obj['SH000016'])
    for symbol in long_targets+short_targets:
        length = len(data_obj[symbol])
        assert length <= basis_length
        print("bias: %d, first: %s" % (basis_length-length, data_obj[symbol][0]['time']))
        assert data_obj[symbol][0]['time'] == data_obj['SH000016'][basis_length-length]['time']
        data_obj[symbol] = [None] * (basis_length - length) + data_obj[symbol]

    f = open('wavediff.json', 'w')
    f.write(json.dumps(data_obj))
    f.close


def compute_earning():
    # parameters
    long_lever = 1.0
    short_lever = 1.0
    top_long_count = 1
    top_short_count = 1
    test_fund = 500000.0
    compound_mode = True #False
    charge_rate = 0.0003

    # global vars
    owning = {} #{"sz50":0, "hs300":0, "zz500":0, "cyb":0}
    cur_earn = 0
    earning = 0
    earning_list = []
    cur_long_pos = {}
    cur_short_pos = {}
    cur_fund = test_fund
    top_fund = test_fund
    nearest_bottom = test_fund
    max_return = 0
    max_return_i = 0
    max_return_time = ""
    max_daily_return = 0

    for d in range(len(data_obj['SH000016'])):
        long_sym_dict = {} # map from percent to symbol, the value is a list because there may be multiple
        long_percents = [] # list of percent values for that day, each value is distinct
        for sym in short_targets:
            if data_obj[sym][d] == None:
                continue
            key = str(data_obj[sym][d]['percent'])
            if key not in long_sym_dict:
                long_sym_dict[key] = [sym]
                long_percents.append(data_obj[sym][d]['percent'])
            else:
                long_sym_dict[key].append(sym)
        long_percents.sort()
        long_percents.reverse()

        short_sym_dict = {} # map from percent to symbol, the value is a list because there may be multiple
        short_percents = [] # list of percent values for that day, each value is distinct
        for sym in short_targets:
            if data_obj[sym][d] == None:
                continue
            key = str(data_obj[sym][d]['percent'])
            if key not in short_sym_dict:
                short_sym_dict[key] = [sym]
                short_percents.append(data_obj[sym][d]['percent'])
            else:
                short_sym_dict[key].append(sym)
        short_percents.sort()

        # calculate the profit of the day
        cur_earn = 0
        for each_owning in list(cur_long_pos.keys()):
            cur_earn += cur_long_pos[each_owning] * data_obj[each_owning][d]['percent'] / 100.0 * long_lever
        for each_owning in list(cur_short_pos.keys()):
            cur_earn -= cur_short_pos[each_owning] * data_obj[each_owning][d]['percent'] / 100.0 * short_lever
        cur_earn -= (cur_fund if compound_mode else test_fund) * charge_rate
        earning += cur_earn
        cur_fund += cur_earn


        # close the current positions
        cur_long_pos = {}
        cur_short_pos = {}

        # determine the positions
        each_long_pos = (cur_fund if compound_mode else test_fund) / (top_long_count * (1 + long_lever/short_lever))
        each_short_pos = (cur_fund if compound_mode else test_fund) / (top_short_count * (1 + short_lever/long_lever))
        max_long_val = long_percents[0]
        min_short_val = short_percents[0]
        if (max_long_val - min_short_val >= 0.0) and (max_long_val - min_short_val < 44):
            # long
            i = 0
            for percent_val in long_percents:
                if i >= top_long_count:
                    break
                for sym in long_sym_dict[str(percent_val)]:
                    if i >= top_long_count:
                        break
                    cur_long_pos[sym] = each_long_pos
                    i += 1

            # short
            i = 0
            for percent_val in short_percents:
                if i >= top_short_count:
                    break
                for sym in short_sym_dict[str(percent_val)]:
                    if i >= top_short_count:
                        break
                    cur_short_pos[sym] = each_short_pos
                    i += 1
        elif max_long_val - min_short_val >= 44:
            # long side (but do short)
            i = 0
            for percent_val in long_percents:
                if i >= top_long_count:
                    break
                for sym in long_sym_dict[str(percent_val)]:
                    if i >= top_long_count:
                        break
                    cur_long_pos[sym] = each_long_pos * -1
                    i += 1

            # short side (but do long)
            i = 0
            for percent_val in short_percents:
                if i >= top_short_count:
                    break
                for sym in short_sym_dict[str(percent_val)]:
                    if i >= top_short_count:
                        break
                    cur_short_pos[sym] = each_short_pos * -1
                    i += 1

        # earning and max return calculation
        earning_list.append(cur_fund)
        if cur_fund > top_fund:
            top_fund = cur_fund
            nearest_bottom = top_fund
        if cur_fund < nearest_bottom:
            nearest_bottom = cur_fund
            if (top_fund - nearest_bottom) / top_fund > max_return:
                max_return = (top_fund - nearest_bottom) / top_fund
                max_return_i = d
                max_return_time = data_obj['SH000016'][d]['time'] + "top_fund: %d, bottom: %d" % (top_fund, nearest_bottom)

        # 
        daily_profit = cur_earn/(cur_fund if compound_mode else test_fund)
        if daily_profit < max_daily_return:
            max_daily_return = daily_profit

        # Output daily report
        output = 'Long- '
        for each in list(cur_long_pos.keys()):
            output += "%s:%.2f," % (each, cur_long_pos[each])
        output += ' Short- '
        for each in list(cur_short_pos.keys()):
            output += "%s:%.2f," % (each, cur_short_pos[each])
        print("[%s] Owning: %s; daily profit: %.3f; total profit: %.3f" % (data_obj['SH000016'][d]['time'][:10]+"-"+data_obj['SH000016'][d]['time'][-4:], output, cur_earn/(cur_fund if compound_mode else test_fund), earning/test_fund))

    print("Avr. daily profit: %f; Max return %f at %d: %s; max_daily_return: %.3f" % (earning/test_fund/len(data_obj['SH000016']), max_return, max_return_i, max_return_time, max_daily_return))
    fig, ax = plt.subplots()
    ax.plot(earning_list)
    ax.grid(True)
    plt.show()


years    = mdates.YearLocator()   # every year
months   = mdates.MonthLocator()  # every month
yearsFmt = mdates.AutoDateFormatter(months)

def compute_rate_avr():
    rate_avr = []
    for i in range(len(sz50)):
        val = 0
        for target in (sz50, hs300, zz500, cyb):
            val += float(target[i]["percent"])
        val /= 4
        rate_avr.append(val)
    print("length is %d" % len(rate_avr))
    return rate_avr

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

