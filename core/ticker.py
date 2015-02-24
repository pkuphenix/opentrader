from common.utils import gen_time, Observable
from common.db import db_ot
from datetime import datetime, timedelta, date, time as daytime
import time

MODE_HISTORY = 0
MODE_REALTIME = 1
class SPEED_MAX:
    pass
class SPEED_REALTIME:
    pass

class TradeCalendar(object):
    open_time = daytime(9, 30)
    close_time = daytime(15, 0)
    cache_dates = {}

    @staticmethod
    def build_date_cache():
        cur_date = None
        last_date = None
        # build the datastructure
        for each in db_ot.xueqiu_k_day.find({'symbol':'SH000001'}):
            last_date = cur_date
            cur_date = each['time'].date()
            TradeCalendar.cache_dates[cur_date] = {'last':last_date, 'next':None}
            if last_date is not None:
                TradeCalendar.cache_dates[last_date]['next'] = cur_date

    @staticmethod
    def check_date(d):
        if not TradeCalendar.cache_dates:
            TradeCalendar.build_date_cache()
            
        if d in TradeCalendar.cache_dates:
            return True
        else:
            return False

class Ticker(Observable):
    def __init__(self, mode=MODE_HISTORY, begin=None, end=None, speed=SPEED_MAX):
        self.initob()
        self.mode = mode
        self.begin = begin
        self.end = end
        self.speed = speed

        assert self.begin.date() < self.end.date() # must at least last one day
        self._now = self.begin

    @property
    def now(self):
        return self._now

    def go(self, t):
        if type(t) is datetime:
            self._now = t
        elif type(t) is date:
            self._now = self._now.replace(t.year, t.month, t.day, 0, 0, 0, 0)
        elif type(t) is daytime:
            self._now = self._now.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=t.microsecond)
        else:
            raise ValueError('invalid datetime object %s' % str(t))
        return self._now

    def first_day_runner(self):
        if not TradeCalendar.check_date(self.now.date()):
            self.go(self.now.date() + timedelta(days=1))
            return

        if self.now.time() <= TradeCalendar.open_time:
            self.go(TradeCalendar.open_time)
            self.fire('day-open')
            

        if self.now.time() >= TradeCalendar.open_time and self.now.time() <= TradeCalendar.close_time:
            self.go(TradeCalendar.close_time)
            self.fire('day-close')

        if self.now.time() > TradeCalendar.close_time:
            self.go(self.now.date() + timedelta(days=1))

    def last_day_runner(self):
        if not TradeCalendar.check_date(self.now.date()):
            return

        if self.end.time() < TradeCalendar.open_time:
            return

        self.go(TradeCalendar.open_time)
        self.fire('day-open')

        if self.end.time() < TradeCalendar.close_time:
            return
        
        self.go(TradeCalendar.close_time)
        self.fire('day-close')
        self.go(self.end)

    def day_runner(self):
        if not TradeCalendar.check_date(self.now.date()):
            self.go(self.now.date() + timedelta(days=1))
            return

        self.go(TradeCalendar.open_time)
        self.fire('day-open')
        self.go(TradeCalendar.close_time)
        self.fire('day-close')
        self.go(self.now.date() + timedelta(days=1))

    def hour_runner(self):
        pass

    def min_runner(self):
        pass

    def sec_runner(self):
        pass

    def run(self):
        # release a event at the beginning of this run
        self.fire('ticker-begin')
        # consume first day
        self.first_day_runner()
        while self.now.date() < self.end.date():
            self.day_runner()
        self.last_day_runner()
        self.fire('ticker-end')


def test_ticker():
    ticker = Ticker(mode=MODE_REALTIME,
                    begin=gen_time('2014-01-01 00:00:00'),
                    end=gen_time('2014-12-31 23:00:00'),
                    speed=SPEED_REALTIME)
    def testrunner(e):
        print '%s: %s' % (e.name, str(e.source.now))
        
    ticker.subscribe('ticker-begin', testrunner)
    ticker.subscribe('ticker-end', testrunner)
    ticker.subscribe('day-open', testrunner)
    ticker.subscribe('day-close', testrunner)
    ticker.run()

