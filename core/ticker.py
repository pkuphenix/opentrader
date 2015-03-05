from common.utils import gen_time, Observable
from common.db import db_ot
from datetime import datetime, timedelta, date, time as daytime
import time, threading

class TradeCalendar(object):
    open_time = daytime(9, 30)
    close_time = daytime(15, 0)
    cache_dates = {}
    _cache_latest_date = None
    _cache_build_date = None

    @staticmethod
    def build_date_cache():
        today = date.today()
        cur_date = None
        last_date = None
        # build the datastructure
        for each in db_ot.xueqiu_k_day.find({'symbol':'SH000001'}):
            last_date = cur_date
            cur_date = each['time'].date()
            TradeCalendar.cache_dates[cur_date] = {'last':last_date, 'next':None}
            if last_date is not None:
                TradeCalendar.cache_dates[last_date]['next'] = cur_date
        TradeCalendar._cache_latest_date = cur_date
        # add today if it is not inside cache
        if not today in TradeCalendar.cache_dates:
            assert cur_date is not None
            TradeCalendar.cache_dates[cur_date]['next'] = today
            TradeCalendar.cache_dates[today] = {'last':cur_date, 'next':None}
            TradeCalendar._cache_latest_date = today
        TradeCalendar._cache_build_date = today

    @staticmethod
    def check_date(d):
        if not TradeCalendar.cache_dates or date.today() > TradeCalendar._cache_build_date:
            TradeCalendar.build_date_cache()
            
        if d in TradeCalendar.cache_dates:
            return True
        else:
            return False

    @staticmethod
    def get_date(base, bias):
        if not TradeCalendar.cache_dates or date.today() > TradeCalendar._cache_build_date:
            TradeCalendar.build_date_cache()
            
        # find the base from the cache_dates
        if base not in TradeCalendar.cache_dates:
            return None
        else:
            d = base
            b = bias
            while d is not None:
                if b > 0:
                    d = TradeCalendar.cache_dates[d]['next']
                    b -= 1
                elif b < 0:
                    d = TradeCalendar.cache_dates[d]['last']
                    b += 1
                else:
                    break
            return d

    @staticmethod
    def get_latest_date_before(base):
        if not TradeCalendar.cache_dates or date.today() > TradeCalendar._cache_build_date:
            TradeCalendar.build_date_cache()
            
        d = TradeCalendar._cache_latest_date
        while d is not None:
            if base >= d:
                return d
            else:
                d = TradeCalendar.cache_dates[d]['last']
        return d




class Ticker(Observable):
    def __init__(self, begin=None, end=None):
        self.initob()
        self.begin = begin
        self.end = end

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

    def _first_day_runner(self):
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

    def _last_day_runner(self):
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

    def _day_runner(self):
        if not TradeCalendar.check_date(self.now.date()):
            self.go(self.now.date() + timedelta(days=1))
            return

        self.go(TradeCalendar.open_time)
        self.fire('day-open')
        self.go(TradeCalendar.close_time)
        self.fire('day-close')
        self.go(self.now.date() + timedelta(days=1))

    def _hour_runner(self):
        pass

    def _min_runner(self):
        pass

    def _sec_runner(self):
        pass

    def run(self):
        # release a event at the beginning of this run
        self.fire('ticker-begin')
        # consume first day
        self._first_day_runner()
        while self.now.date() < self.end.date():
            self._day_runner()
        self._last_day_runner()
        self.fire('ticker-end')

    def bias(self):
        return 0

class RealtimeTicker(Observable):
    def __init__(self):
        self.initob()
        self._now = datetime.now()
        self._thread = RealtimeTicker.TickerThread(self)

    @property
    def now(self):
        return self._now

    def go(self, t):
        raise AssertionError('Realtime ticker could not be played as a time machine :)')

    def _step(self):
        self._now += timedelta(seconds=1)

    class TickerThread(threading.Thread):
        def __init__(self, ticker):
            super(RealtimeTicker.TickerThread, self).__init__()
            self.cancelled = False
            self.ticker = ticker
            self._hour_ignore = False
            self._day_ignore = False

        def run(self):
            """Overloaded Thread.run, runs the update 
            method once per every 10 milliseconds."""
            while not self.cancelled:
                self.update_second()
                # try to fix the bias                
                if self.ticker.bias < timedelta(seconds=1):
                    time.sleep((timedelta(seconds=1) - self.ticker.bias).microseconds / 1000000.0)
                self.ticker._step()

        # called every software second
        def update_second(self):
            if self.ticker.now.second == 0:
                self.update_minute()

        def update_minute(self):
            if self.ticker.now.minute == 0:
                self.update_hour() # may set _hour_ignore

            if not self._hour_ignore and not self._day_ignore:
                if self.ticker.now.time() == TradeCalendar.open_time:
                    self.ticker.fire('day-open')
                if self.ticker.now.time() == TradeCalendar.close_time:
                    self.ticker.fire('day-close')

        def update_hour(self):
            if self.ticker.now.hour == 0:
                self.update_day() # may set _day_ignore

        def update_day(self):
            if not TradeCalendar.check_date(self.ticker.now.date()):
                self._day_ignore = True
            else:
                self._day_ignore = False

        def cancel(self):
            """End this timer thread"""
            self.cancelled = True

    def run(self):
        # release a event at the beginning of this run
        self.fire('ticker-begin')
        self._now = datetime.now()
        # create a new thread to run the ticker
        self._thread.start()
        #self.fire('ticker-end')

    def stop(self):
        self._thread.cancel()
        self._thread.join(1)

    # bias means how much real-world time is faster than the ticker's time
    @property
    def bias(self):
        return datetime.now() - self.now

RT = RealtimeTicker()

def test_ticker():
    ticker = Ticker(begin=gen_time('2014-01-01 00:00:00'),
                    end=gen_time('2014-12-31 23:00:00'))
    def testrunner(e):
        print '%s: %s' % (e.name, str(e.source.now))
        
    ticker.subscribe('ticker-begin', testrunner)
    ticker.subscribe('ticker-end', testrunner)
    ticker.subscribe('day-open', testrunner)
    ticker.subscribe('day-close', testrunner)
    ticker.run()

def test_realtime_ticker():
    rt = RealtimeTicker()
    rt.run()
    i = 0
    while i < 10:
        print rt.now
        print rt.bias
        time.sleep(1)
        i += 1
    rt.stop()

def test_calendar():
    test_date1 = gen_time('2015-03-02 00:00:00').date()
    test_date2 = gen_time('2015-02-26 00:00:00').date()
    test_date3 = gen_time('2015-02-27 00:00:00').date()
    test_date4 = gen_time('2015-03-01 00:00:00').date()
    assert TradeCalendar.get_date(test_date1, -2) == test_date2
    assert TradeCalendar.get_latest_date_before(test_date4) == test_date3
    assert TradeCalendar.get_latest_date_before(test_date1) == test_date1


