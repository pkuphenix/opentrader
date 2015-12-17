import time, requests
from datetime import datetime
from opentrader.common.utils import gen_tick
from common.exceptions import InvalidSymbol
import json
PREFIX1 = 'http://hqdigi2.eastmoney.com'

# em code "0000011, 0000012" - last byte for market
# into standard symbol: SH000001, SZ000001
def emcode_to_symbol(symbol):
    if symbol[-1] == '1':
        return 'SH' + symbol[:-1]
    if symbol[-1] == '2':
        return 'SZ' + symbol[:-1]
    else:
        return None

class EMAPI(object):
    one_min_cache = None
    one_min_cache_time = time.time()
            
    def __init__(self):
        pass

    #/EM_Quote2010NumericApplication/index.aspx
    # ?type=s
    # &sortType=C
    # &sortRule=-1
    # &pageSize=5000&page=1
    # &jsName=quote_123
    # &style=33
    # &token=44c9d251add88e27b65ed86506f6e5da
    # &_g=0.8833715715445578
    # ------------------------------------------
    # sortType=C 涨跌幅 A 股票代码
    # sortRule=-1 逆序 1 正序
    # style=33 沪深个股 32 沪深指数 (000,399开头) 31 场内基金 
    # _g 应该是用于防止cache的
    # token的获得尚不清楚
    # ------------------------------------------
    # 结果格式：
    # "0022422, (最后一位1表示沪市、2表示深市)
    # 002242,
    # 九阳股份,
    # 19.05,昨收
    # 19.25,今开
    # 20.05,最新
    # 20.50,最高
    # 19.15,最低
    # 63350,成交额（亿元）amount
    # 319434,成交量（手）volume
    # 1.00,涨幅（价格）
    # 5.25%,涨幅
    # 19.83,均价
    # 7.09%,
    # 29.39%,委比
    # 1370,委差
    # 2414,逐笔量
    # 128009,
    # 191425,
    # -1,
    # 1,
    # 0.00%,
    # 1.95,
    # 4.20%,
    # 33.40,
    # 001164|002456|003535|003568|003569|003596|003665|003681|003701|5009|50015,
    # 20.04,
    # 20.05,
    # 2015-06-12 15:05:00,
    # 0,
    # 760950016,
    # 14496097224,
    # 22.54"
    def _query_instant(self, sort_type='C', sort_rule='-1', style="33"):
        url = PREFIX1+'/EM_Quote2010NumericApplication/index.aspx'+\
              '?type=s&pageSize=5000&page=1&jsName=quote_123'+\
              '&token=44c9d251add88e27b65ed86506f6e5da&_g=0.8833715715445578'+\
              '&sortType=' + sort_type +\
              '&sortRule=' + sort_rule +\
              '&style=' + style

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-CN, zh-Hans; q=0.8, en-US; q=0.5, en; q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'Referer': 'http://www.eastmoney.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko',
            'X-Requested-With': 'XMLHttpRequest',
        }
        print(url)
        r = requests.get(url, headers=headers)
        # var quote_123={rank:["","","",...],pages:1}
        resp_txt = r.text[20:-9]
        resp_json = json.loads(resp_txt)
        rtn = []
        for item_text in resp_json:
            # each item is a string
            item = item_text.split(',')
            item_dict = {
                "symbol": emcode_to_symbol(item[0]),
                "code": item[1],
                "name": item[2],
                "last_close": float(item[3]),
                "open": float(item[4]),
                "current": float(item[5]),
                "high": float(item[6]),
                "low": float(item[7]),
                "amount": float(item[8]),
                "volume": int(item[9]),
                "change": float(item[10]),
                "percent": float(item[11][:-1]),
                "avr": float(item[12]),
            }
            rtn.append(item_dict)
        return rtn


def test_em():
    api = EMAPI()
    print(api._query_instant())


