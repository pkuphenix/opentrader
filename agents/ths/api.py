import time, requests, json
from datetime import datetime
from opentrader.common.utils import gen_tick
from opentrader.common.exceptions import InvalidSymbol
PREFIX1 = 'http://www.iwencai.com'
PREFIX2 = 'http://d.10jqka.com.cn/v2'

# standard symbol: SH000001, SZ000001
# into 10jqka symbol: sh_000001, hs_000001
# All "SH00xxxx" are converted into "1Axxxx"
def symbol_convert(symbol):
    if symbol[:4] == 'SH00':
        return 'hs_1A' + symbol[4:]
    if symbol[:2] in ('SH', 'SZ'):
        return 'hs_' + symbol[2:]
    else:
        return None

# Drop SH/SZ from standard symbol
def symbol_convert2(symbol):
    if symbol[:4] == 'SH00':
        return '1A' + symbol[4:]
    if symbol[:2] in ('SH', 'SZ'):
        return symbol[2:]
    else:
        return None

# 000539.SZ into SZ000539, 600652.SH into SH600652
def symbol_convert3(symbol):
    if symbol[-2:] in ('SH', 'SZ'):
        return symbol[-2:] + symbol[:-3]
    else:
        return None

class THSAPI(object):
    one_min_cache = None
    one_min_cache_time = time.time()
            
    def __init__(self):
        self.sess = requests.Session()

    #http://d.10jqka.com.cn/v2/time/sh_600519/last.js
    #http://d.10jqka.com.cn/v2/line/hs_000488/00/last.js
    #http://d.10jqka.com.cn/v2/line/sh_600015/21/today.js
    #http://d.10jqka.com.cn/v2/line/hs_000001/21/2014.js
    #URL代码含义：
    #第一位：0 日k线，1周k线，2月k线，3－5分钟线，4 － 半小时线，5-小时线，6-分钟线，7？？
    #（对于last.js接口，周、月k线为全部数据，其他均为最后140项数据，另外，只有日周月k数据是全的，其他均不全。数据仅有［开收高低量额幅］其他所有指标均为前端计算得来）
    #第二位：0 不复权，1前复权（默认），2后复权
    def _get_market_data(self, symbol, time_or_line='line', query="last.js", flag="01"):
        sym = symbol_convert(symbol)
        if not sym:
            raise InvalidSymbol('invalid symbol: %s' % (symbol))

        url = PREFIX2+'/'+time_or_line+'/'+sym+'/'+flag+'/'+query
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-CN, zh-Hans; q=0.8, en-US; q=0.5, en; q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'Referer': 'http://www.iwencai.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko',
            'X-Requested-With': 'XMLHttpRequest',
        }
        r = requests.get(url, headers=headers)
        txt = r.text
        i = txt.find('\"data\":\"')
        return txt[i+8:-3]

    # get the latest stock analyzing data by iwencai
    # find {'data':{'data':{'result':{'event':..., buy':..., 'sell':..., 'zxst':...}}}}
    # and each "..." above looks like: {'<somecode>':{'query':'<flag_name>'}, ...}
    URL_ANALYZE = "http://www.iwencai.com/diag/block-detail?pid=8073&codes=%s&codeType=stock&info=%%7B%%22view%%22%%3A%%7B%%22nolazy%%22%%3A1%%2C%%22parseArr%%22%%3A%%7B%%22qType%%22%%3A%%22STOCK%%22%%2C%%22query%%22%%3A%%22hs_%s%%22%%2C%%22rlt%%22%%3A%%7B%%22nodes%%22%%3A%%5B%%7B%%22text%%22%%3A%%22%s%%22%%2C%%22type%%22%%3A%%22STR_VAL%%22%%2C%%22ofWhat%%22%%3A%%22_%%5Cu80a1%%5Cu7968%%5Cu4ee3%%5Cu7801%%22%%2C%%22id%%22%%3A%%22%s%%22%%2C%%22index%%22%%3A%%223%%22%%2C%%22idList%%22%%3A%%5B%%22%s%%22%%5D%%7D%%5D%%7D%%2C%%22staying%%22%%3A%%5B%%5D%%2C%%22newParserJsonStr%%22%%3A%%22++++++++%%5C%%22%%5Cu80a1%%5Cu7968%%5Cu4ee3%%5Cu7801_%s%%5C%%22%%2C%%5C%%22%%5Cu80a1%%5Cu7968%%5Cu4ee3%%5Cu7801_%s%%5C%%22%%2C%%5C%%22%%5Cu80a1%%5Cu7968%%5Cu4ee3%%5Cu7801_%s%%5C%%22++++%%22%%7D%%2C%%22asyncParams%%22%%3A%%7B%%22env%%22%%3Anull%%2C%%22tid%%22%%3A%%22137%%22%%7D%%7D%%7D"
    def _get_stock_analyze(self, symbol):
        sym = symbol_convert2(symbol)
        if not sym:
            raise InvalidSymbol('invalid symbol: %s' % (symbol))

        url = self.URL_ANALYZE % (sym,sym,sym,sym,sym,sym,sym,sym)
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-CN, zh-Hans; q=0.8, en-US; q=0.5, en; q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'Referer': 'http://www.iwencai.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko',
            'X-Requested-With': 'XMLHttpRequest',
        }
        r = requests.get(url, headers=headers)
        return json.loads(r.text)

    URL_IWENCAI_QUERY = "http://www.iwencai.com/stockpick/search?typed=1&preParams=&ts=1&perpage=4000&f=1&qs=1&selfsectsn=&querytype=&searchfilter=&tid=stockpick&w=%s"
    #URL_IWENCAI_QUERY_EXPORT = "http://www.iwencai.com/stockpick/export?token=%s"
    # query iwencai and get a full stock symbol list
    def query_iwencai(self, query):
        url = self.URL_IWENCAI_QUERY % (query)
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-CN, zh-Hans; q=0.8, en-US; q=0.5, en; q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'Referer': 'http://www.iwencai.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko',
            'X-Requested-With': 'XMLHttpRequest',
        }
        #print(url)
        r = requests.get(url, headers=headers)
        # look for: "token":"3c056e348add1a00a81b17e2ec4280b4"
        lines = r.text.split('\n')
        for line in lines:
            if line.find("allResult") > 0:
                # eat up final characters that is not '}'
                result = line[16:-1]
                while result[-1] != '}':
                    result = result[:-1]
                return json.loads(result)
        return None

def test_ths():
    api = THSAPI()
    #print(api._get_market_data('SH000001'))
    print(api._get_stock_analyze('SZ002345'))
    print(api.query_iwencai('2004年1月1日光头阳线'))


