import time, urllib, urllib2, json, cookielib, sys
from datetime import datetime
PREFIX = 'http://xueqiu.com'

def dict_to_param(dict):
    return '?' + '&'.join(['%s=%s' % (key, str(value)) for (key, value) in dict.iteritems()])

def current_tick():
    return int(time.time() * 1000)

def is_tick(val):
    if type(val) in (int, long):
        return True
    else:
        return False

# str_time: "2010-06-04 21:08:12"
def gen_tick(str_time, precision=1):
    return int(time.mktime(time.strptime(str_time, "%Y-%m-%d %H:%M:%S")) * precision)

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
        self._cj = cookielib.CookieJar()
        self._urlopen(PREFIX) # to initialize the cookie jar

    def _urlopen(self, url):
        req = urllib2.Request(url)
        req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cj))
        return opener.open(req)

    def _urlpost(self, url, data):
        req = urllib2.Request(url)
        req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
        data = urllib.urlencode(data)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cj))
        return opener.open(req, data)

    def captcha_get(self, file_path):
        resp = self._urlopen(PREFIX + '/service/captcha/id').read()
        img = self._urlopen(PREFIX + '/service/captcha/img?_=' + str(current_tick())).read()
        return open(file_path, 'wb').write(img)

    def captcha_post(self, char):
        resp = self._urlpost(PREFIX + '/service/captcha', {'code':char}).read()
        return resp

    def stock_list(self, orderby='code'):
        # http://xueqiu.com/stock/cata/stocklist.json
        # ?page=10&size=90&order=desc&orderby=percent&type=11%2C12&_=1420879504733
        params = {
            'page': 1,
            'size': 90,
            'orderby': orderby,
            'type': '11%2C12',
            '_': current_tick()
        }
        url = PREFIX + '/stock/cata/stocklist.json' + dict_to_param(params)
        resp = self._urlopen(url).read()
        resp_json = json.loads(resp)
        final_resp = resp_json['stocks']

        count = int(resp_json['count']['count'])
        assert count > 5000
        sys.stdout.write('Querying %u pages .' % (count / 90 + 1))
        sys.stdout.flush()
        while params['page'] <= (count / 90):
            params['page'] += 1
            url = PREFIX + '/stock/cata/stocklist.json' + dict_to_param(params)
            resp = self._urlopen(url).read()
            resp_json = json.loads(resp)
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
        resp_json = json.loads(resp)
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
            resp_json = json.loads(resp)
        except ValueError:
            print resp
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
            resp_json = json.loads(resp)
        except ValueError:
            raise ValueError('response not a valid JSON: %s' % resp)
        return resp_json['quotes']

def test_stock_list():
    xueqiu = XueqiuAPI()
    #resp = xueqiu.stock_list()
    #assert len(resp) > 5000

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

