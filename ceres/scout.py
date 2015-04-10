from common.utils import gen_time, Observable, AntiDupPool
from common.db import db_ot
from datetime import datetime, timedelta, date, time as daytime
import time
from collections import OrderedDict
from core.ticker import Ticker,TradeCalendar
from core.stock import Stock
from core.query import QuerySet
import ceres.probe as probe

# A scout is in charge of firing openning events(signals) for specific stock:
# open-long, open-short
class Scout(Observable):
    def __init__(self, *args, **kwargs):
        self.probes = []
        self.initob()
        self.init(*args, **kwargs)

    def init(self, *args, **kwargs):
        pass # to be overwritten by sub classes

    def bind_ticker(self, ticker):
        self._ticker = ticker
        if hasattr(self, '_day_close'):
            ticker.subscribe('day-close', getattr(self, '_day_close'))
        # bind ticker for all probes
        for each_probe in self.probes:
            each_probe.bind_ticker(ticker) # in this function, ticker events are
                                           # are also bound to probes
    # called by sub classes
    def add_probe(self, probe):
        self.probes.append(probe)

    # shortcuts for stock markets
    def _fire_long(self, symbols):
        self.fire('open-long', symbols=symbols, time=self._ticker.now)

    def _fire_short(self, symbols):
        self.fire('open-short', symbols=symbols, time=self._ticker.now)

class Newhigh55Scout(Scout):
    def init(self):
        self.recent_newhigh = AntiDupPool(10)
        p = probe.Newhigh55Probe()
        p.set_entry_auto_all(autoquery=False)
        self.add_probe(p)
        p.subscribe('probe-detect', getattr(self, '_on_detect'))

    def _on_detect(self, detect_event):
        pure_newhigh = self.recent_newhigh.filter(detect_event.symbols)
        self._fire_long(pure_newhigh)


def test_newhigh55scout():
    ticker = Ticker(begin=gen_time("2014-11-01 00:00:00"), end=gen_time("2015-03-01 00:00:00"))
    s = Newhigh55Scout()
    def ticker_printer(e):
        print e.source.now.date()
    ticker.subscribe('day-close', ticker_printer)
    s.bind_ticker(ticker)

    gr = probe.PercentRecorder('global', 10)
    gr_days = probe.PercentRecorder('global_days', 10)
    def scout_fired(e):
        #tom_date = TradeCalendar.get_date(e.time.date(),5)
        yes_date = TradeCalendar.get_date(e.time.date(),-1)
        dr = probe.PercentRecorder('daily')
        dr_days = probe.PercentRecorder('daily_days')
        for symbol in e.symbols:
            yesk = db_ot.xueqiu_k_day.find_one({'symbol':symbol,'time':datetime(yes_date.year,yes_date.month,yes_date.day)})
            tomk0 = db_ot.xueqiu_k_day.find_one({'symbol':symbol,'time':datetime(e.time.date().year,e.time.date().month,e.time.date().day)})
            tomk = db_ot.xueqiu_k_day.find({'symbol':symbol,'time':{'$gt':datetime(e.time.date().year,e.time.date().month,e.time.date().day)}})
            
            if tomk0['percent'] > 9:
                continue
            if yesk and tomk0['volume'] / yesk['volume'] > 2.0:
                pass
            else:
                continue

            buy = tomk0['close']
            sell = tomk0['close']
            risk = 2 * tomk0['atr20']
            hold_days = 0

            if tomk:
                last_low5 = tomk0['low5']
                for dayk in tomk:
                    hold_days += 1
                    if dayk['low'] <  buy-risk:
                        # reach the -R in this day
                        sell = buy-risk
                        break
                    if dayk['low'] < last_low5:
                        sell = dayk['close']
                        break
                    last_low5 = dayk['low5']

                #dr.record(tomk['percent'])
                #gr.record(tomk['percent'])
                dr.record((sell-buy)/buy*100)
                gr.record((sell-buy)/buy*100)
                dr_days.record(float(hold_days))
                gr_days.record(float(hold_days))

        gr.eat_ignore()
        gr_days.eat_ignore()
        dr.show()
        gr.show()
        dr_days.show()
        gr_days.show()

    s.subscribe('open-long', scout_fired)
    ticker.run()



