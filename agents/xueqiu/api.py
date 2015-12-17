# -*- coding: utf-8 -*-
import time, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, json, http.cookiejar, sys
from datetime import datetime
from opentrader.common.utils import gen_tick
PREFIX = 'http://xueqiu.com'

def dict_to_param(dict):
    return '?' + '&'.join(['%s=%s' % (key, str(value)) for (key, value) in list(dict.items())])

def current_tick():
    return int(time.time() * 1000)

def is_tick(val):
    if type(val) in (int, int):
        return True
    else:
        return False

# datetime.strptime('Fri Jan 09 15:09:53 +0800 2015', '%a %b %d %H:%M:%S +0800 %Y')
# parse the time format by xueqiu into standard datetime instance
def time_parse(time_str):
    # XXX remove the timezones: +0800 or -0500
    time_str = time_str[:-10] + time_str[-4:]
    return datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y')


class XueqiuAPI(object):
    one_min_cache = None
    one_min_cache_time = time.time()

    @staticmethod
    def get_api():
        if time.time()-XueqiuAPI.one_min_cache_time < 60 and XueqiuAPI.one_min_cache is not None:
            return XueqiuAPI.one_min_cache
        else:
            XueqiuAPI.one_min_cache = XueqiuAPI()
            XueqiuAPI.one_min_cache_time = time.time()
            return XueqiuAPI.one_min_cache
            
    def __init__(self):
        self._cj = http.cookiejar.CookieJar()
        self._urlopen(PREFIX) # to initialize the cookie jar

    def _urlopen(self, url):
        req = urllib.request.Request(url)
        req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cj))
        return opener.open(req)

    def _urlpost(self, url, data):
        req = urllib.request.Request(url)
        req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
        data = urllib.parse.urlencode(data)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cj))
        return opener.open(req, data)

    def captcha_get(self, file_path):
        resp = self._urlopen(PREFIX + '/service/captcha/id').read()
        img = self._urlopen(PREFIX + '/service/captcha/img?_=' + str(current_tick())).read()
        return open(file_path, 'wb').write(img)

    def captcha_post(self, char):
        resp = self._urlpost(PREFIX + '/service/captcha', {'code':char}).read()
        return resp

    # {"count": {"count":4091.0}, "success":"true", "stocks":[
    #    {"symbol":"SH900955","code":"900955","name":"九龙山B",
    #     "current":"0.998","percent":"0.0",
    #     "change":"0.0","high":"0.0","low":"0.0",
    #     "high52w":"1.036","low52w":"0.37",
    #     "marketcapital":"1.300893E9","amount":"0.0",
    #     "pettm":"2749.52","volume":"0","hasexist":"false"},...]}
    def stock_list(self, orderby='code', type=('11','12')):
        # http://xueqiu.com/stock/cata/stocklist.json
        # ?page=10&size=90&order=desc&orderby=percent&type=11%2C12&_=1420879504733
        #
        # [TODO]
        # 雪球行业
        # http://xueqiu.com/stock/cata/stocklist.json
        # ?page=1&size=30&order=desc&orderby=percent&exchange=CN
        # &plate=%E4%BC%A0%E5%AA%92&_=1443645842141       传媒
        #
        # 证监会行业
        # http://xueqiu.com/industry/quote_order.json
        # ?page=1&size=30&order=desc&exchange=CN
        # &plate=%E5%AE%B6%E5%85%B7%E5%88%B6%E9%80%A0%E4%B8%9A 家具制造业
        # &orderBy=percent&level2code=C21&_=1443646077513
        # 
        # 基础分类：创业板cyb/中小板zxb/sha/shb/sza/szb
        # http://xueqiu.com/stock/quote_order.json?page=1&size=30&order=desc
        # &exchange=CN&stockType=sha
        # &column=symbol%2Cname%2Ccurrent%2Cchg%2Cpercent%2Clast_close%2Copen%2Chigh%2Clow%2Cvolume%2Camount%2Cmarket_capital%2Cpe_ttm%2Chigh52w%2Clow52w%2Chasexist&orderBy=percent&_=1443646275396
        params = {
            'page': 1,
            'size': 90,
            'orderby': orderby, # code | percent | ...
            'type': '%2C'.join(type),
            # 0: Test Stocks
            # 1: 美股中概股
            # 2: 美股
            # 3: 美股指数
            # 11: A股
            # 12: A股指数 399*
            # 13: A股基金 15* 51*
            # 15: 债券
            # 16: 债券
            # 20: 信托
            # 22: 理财
            # 23: 场外基金
            # 30: 港股
            # 32: ？？
            '_': current_tick()
        }
        url = PREFIX + '/stock/cata/stocklist.json' + dict_to_param(params)
        resp = self._urlopen(url).read()
        resp_json = json.loads(resp.decode('utf8'))
        final_resp = resp_json['stocks']

        count = int(resp_json['count']['count'])
        sys.stdout.write('Querying %u pages .' % (count / 90 + 1))
        sys.stdout.flush()
        while params['page'] <= (count / 90):
            params['page'] += 1
            url = PREFIX + '/stock/cata/stocklist.json' + dict_to_param(params)
            resp = self._urlopen(url).read()
            resp_json = json.loads(resp.decode('utf8'))
            final_resp.extend(resp_json['stocks'])
            sys.stdout.write('.')
            sys.stdout.flush()

        return final_resp

    # period: 1d/5d/6m/all
    def stock_price(self, symbol=None, period='1d'):
        params = {
            'symbol': symbol,
            'period': period,
            '_': current_tick()
        }
        url = PREFIX + '/stock/forchart/stocklist.json' + dict_to_param(params)
        resp = self._urlopen(url).read()
        resp_json = json.loads(resp.decode('utf8'))
        return resp_json['chartlist']

    def stock_k_day(self, symbol=None, atype='normal', begin=None, end=None):
        if end is None:
            end = current_tick()
        else:
            if not is_tick(end):
                end = gen_tick(end, precision=1000)

        if begin is None:
            begin = end - 365 * 24 * 3600 * 1000 # 1 year ago till now
        else:
            if not is_tick(begin):
                begin = gen_tick(begin, precision=1000)
        params = {
            'symbol': symbol,
            'period': '1day',
            'type': atype,
            'begin': begin,
            'end': end,
            '_': current_tick()
        }
        url = PREFIX + '/stock/forchartk/stocklist.json' + dict_to_param(params)
        resp = self._urlopen(url).read()
        try:
            resp_json = json.loads(resp.decode('utf8'))
        except ValueError:
            print(resp)
            raise
        return resp_json['chartlist']

    def stock_instant(self, symbols=[]):
        params = {
            'code': ','.join(symbols),
            '_': current_tick()
        }
        url = PREFIX + '/stock/quote.json' + dict_to_param(params)
        resp = self._urlopen(url).read()
        try:
            resp_json = json.loads(resp.decode('utf8'))
        except ValueError:
            raise ValueError('response not a valid JSON: %s' % resp)
        return resp_json['quotes']

XueqiuAgent = XueqiuAPI

def test_stock_list():
    xueqiu = XueqiuAPI()
    resp = xueqiu.stock_list()
    assert len(resp) > 4000

    resp = xueqiu.stock_price('SH000001')
    assert len(resp) > 100

    resp = xueqiu.stock_k_day('SH000001')
    assert len(resp) > 200

    resp = xueqiu.stock_instant(['SH000001'])
    assert resp[0]['symbol'] == 'SH000001'

    resp = xueqiu.stock_instant(['SH000001'] * 100)
    assert len(resp) == 100

if __name__ == "__main__":
    test_stock_list()

