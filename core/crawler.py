# use various agents to fetch market data
# clean the data to fit the requirement of our standard DB storage
# so sometimes when we don't wanna use DB, we can directly use methods here
from opentrader.agents.xueqiu.api import *
from opentrader.agents.ths.api import *

class Crawler(object):
    pass

class CNCrawler(Crawler):
    _market = "CN"

    def __init__(self):
        self.xueqiu = XueqiuAPI()
        self.ths = THSAPI()

    def get_stock_list(self, cls="A"):
        result = []
        stocks = self.xueqiu.stock_list()
        for stock in stocks:
            if stock['symbol'][:5] in ('SH900'):
                continue
            else:
                result.append(stock)
        return result

    def get_k_day(self, symbol, begin=None, end=None):
        kday_data = self.xueqiu.stock_k_day(symbol=symbol, begin=begin, end=end)
        for each in kday_data:
            each['date'] = datetime.strptime(each['time'], "%a %b %d %H:%M:%S +0800 %Y").date()
        return kday_data

    # get available flags from iwencai
    def get_available_flags(self):
        flags = []
        # first get a latest full list of stocks
        stock_list = self.get_stock_list()
        # then for each stock, get latest flags
        for i,stock in enumerate(stock_list):
            print('Querying stock %d, %s...' % (i, stock['symbol']))
            try:
                result = self.ths._get_stock_analyze(stock['symbol'])
            except InvalidSymbol:
                continue
            for key in ('event','buy','sell','zxst'):
                flag_dict = result['data']['data']['result'][key]
                for flag_item in flag_dict.items():
                    flag = flag_item['query']
                    if flag not in flags:
                        print('Adding new flag: %s' % flag)
                        flags.append(flag)
        print("Got totally %d flags: %s" % (len(flags), flags))


