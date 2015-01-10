import time, urllib2, json, cookielib, sys
PREFIX = 'http://xueqiu.com'

def dict_to_param(dict):
	return '?' + '&'.join(['%s=%s' % (key, str(value)) for (key, value) in dict.iteritems()])

def current_tick():
	return str(int(time.time() * 1000))

class XueqiuAPI(object):
	def __init__(self):
		self._cj = cookielib.CookieJar()
		self._urlopen(PREFIX) # to initialize the cookie jar

	def _urlopen(self, url):
		req = urllib2.Request(url)
		req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cj))
		return opener.open(req)

	def stocklist(self, orderby='code'):
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

def test_stocklist():
	xueqiu = XueqiuAPI()
	resp = xueqiu.stocklist()
	assert len(resp) > 5000

