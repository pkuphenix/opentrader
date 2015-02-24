from common.utils import gen_time, Observable
from common.db import db_ot
from datetime import datetime, timedelta, date, time as daytime
import time

class ProbeImplementError(Exception):
    pass

class Probe(Observable):
    def __init__(self, **kwargs):
        self.entries = [] # each entry is (stock_symbol, datetime)
        self.entry_auto_all = False
        self.init(**kwargs)

    def init(self, **kwargs):
        pass # to be overwritten by sub classes

    def set_entries(self, entries):
        self.entries = entries

    def append_entries(self, entries):
        self.entries.extends(entries)

    # get all available k_day entries
    # from database for specific date
    def _get_all_entries(self, date):
        assert type(date) is date
        res = db_ot.xueqiu_k_day.find({'time':datetime(date.year, date.day)})

    def set_entry_auto_all(self):
        self.entry_auto_all = True

    def bind_ticker(self, ticker)
        if hasattr(self, '_day_close'):
            ticker.subscribe('day-close', getattr(self, 'day_close'))

    def day_close(self, ticker_event):
        if self.entry_auto_all:
            self._get_all_entries(ticker_event.source.now.date())
        self._day_close()

    def _day_close(self, ticker_event):
        raise ProbeImplementError


class BreakProbe(Probe):
    def init(self, period=20, mutex=5):
        self.period = period
        self.mutex = mutex

    def _day_close(self, ticker_event):
        time = ticker_event.source.now
        date = time.date()
        res = db_ot.xueqiu_k_day.find({'time':datetime(date.year, date.day), 'percent':{'$gte':9}})
        entries = []
        for each in res:
            entries.append(each['symbol'])
        self.fire('probe-detect', entries=entries, time=time)

# A scout is in charge of firing openning events(signals) for specific stock:
# open-long, open-short
class Scout(Observable):
    def __init__(self):
        self.probes = []
        self.init(self)

    def set_ticker(self, ticker):
        self._ticker = ticker
        # bind ticker for all probes
        for each_probe in self.probes:
            each_probe.bind_ticker(ticker)

    def add_probe(self, probe):
        self.probes.append(probe)

    # shortcuts for stock markets
    def fire_long(self):
        self.fire('open-long')

    def fire_short(self):
        self.fire('open-short')


class TestScout(Scout):
    def init(self):
        probe = BreakProbe()
        self.






