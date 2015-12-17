import time, requests
from datetime import datetime
from opentrader.common.utils import gen_tick
PREFIX = 'https://trade.gf.com.cn'

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


class NXBAPI(object):
    one_min_cache = None
    one_min_cache_time = time.time()
            
    def __init__(self, dse_sessionid, jsessionid, userId):
        self.dse_sessionid = dse_sessionid
        self.jsessionid = jsessionid
        self.userId = userId
        #self._urlopen(PREFIX) # to initialize the cookie jar

    def _query_entry(self, classname, method, args={}):
        url = PREFIX+'/entry'
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-CN, zh-Hans; q=0.8, en-US; q=0.5, en; q=0.3',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://trade.gf.com.cn/workbench/index.jsp',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko',
            'X-Requested-With': 'XMLHttpRequest',
        }
        cookies = {
            'dse_sessionid': self.dse_sessionid,
            'JSESSIONID': self.jsessionid,
            'name': 'value',
            'userId': self.userId,
        }
        data = {
            'classname': classname,
            'dse_sessionid': self.dse_sessionid,
            'method': method,
        }
        for key, value in args.items():
            data[key] = value

        r = requests.post(url, headers=headers, cookies=cookies, data=data)
        return r


def test_nxb():
    api = NXBAPI('78D9EC2FB51DB768BD79B2F74137928A', '2EE027B31B91CB3B027596790C983E0A', 'd*9E*EE*26*2B*1B*E39*20*E6R*C8*B2*E7*3A*26G*97*883*91G*16bw*22*A05*A8*CCL8G*97*883*91G*16bw*22*A05*A8*CCL8G*97*883*91G*16bw*22*A05*A8*CCL8*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00*00')
    r = api._query_entry('com.gf.etrade.control.FrameWorkControl', 'getStarLevel')
    print(r.status_code)
    print(r.text)


