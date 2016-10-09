import sys
sys.path.append("../../")
import time, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, json, http.cookiejar, sys
from datetime import datetime
from opentrader.common.utils import gen_tick
import random
PREFIX = 'http://q.stock.sohu.com/'

def dict_to_param(dict):
    return '?' + '&'.join(['%s=%s' % (key, str(value)) for (key, value) in dict.items()])

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


class SohuAPI(object):

    @staticmethod
    def get_api():
        if time.time()-SohuAPI.one_min_cache_time < 60 and SohuAPI.one_min_cache is not None:
            return SohuAPI.one_min_cache
        else:
            SohuAPI.one_min_cache = SohuAPI()
            SohuAPI.one_min_cache_time = time.time()
            return SohuAPI.one_min_cache
            
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

    def _market_trans(self, shsz):
        if shsz in ('SH', 'sh'):
            return 'cn'
        elif shsz in ('SZ', 'sz'):
            return 'zs'
        else:
            return ''

    #
    #  ([{"status":0,"hq":[["2011-04-29","2932.48","2911.51","-16.60","-0.57%","2871.01","3067.46","2309860096","272767424.00","-"],
    #                      [...]], "code":"zs_000"
    # each line in "hq": Date, Open, Close, Bias Price, Bias Rate, Low, High, Volume, Amount
    def stock_k_day(self, market, code, start, end):
        url = PREFIX + "/hisHq?code=%s&start=%s&end=%s&stat=0&order=A&period=d&callback=&rt=jsonp&r=" + str(random.random()) + "&" + str(random.random())
        url = url % (self._market_trans(market) + "_" + code, start, end)
        resp = self._urlopen(url).read()
        if len(resp) < 10:
            return {"status":100}
        else:
            resp = resp[2:-3]
        #print resp
        resp_json = json.loads(resp)
        return resp_json



def test_stock_list():
    sohu = SohuAPI()

    resp = sohu.stock_k_day('SZ', '000905', '20140101', '20150803')
    assert resp['status'] == 0


