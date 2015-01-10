from utils import gen_time
from datetime import datetime, timedelta
import time

MODE_HISTORY = 0
MODE_REALTIME = 1
class SPEED_MAX:
	pass
class SPEED_REALTIME:
	pass
class Ticker(object):
	def __init__(self, mode=MODE_HISTORY, begin=None, end=None, speed=SPEED_REALTIME):
		self.mode = mode
		self.begin = begin
		self.end = end
		self.speed = speed

		self._obj = None
		self._method = None
		self._args = []

		self._now = self.begin

	def bind(self, obj, method, args=[]):
		self._obj = obj
		self._method = method
		self._args = args

	def run(self):
		delta = timedelta(seconds=1)
		while self._now < self.end:
			self._now += delta
			# run the bound method
			if self._obj is not None:
				getattr(self._obj, self._method)(*self._args)
			else:
				self._method(*self._args)

			# sleep a while
			if self.speed is SPEED_MAX:
				time.sleep(0.01)
			elif self.speed is SPEED_REALTIME:
				time.sleep(1)
			else:
				pass

	@property
	def now(self):
		return self._now


def test_ticker():
	ticker = Ticker(mode=MODE_REALTIME,
			        begin=gen_time('2014-01-01 09:30:00'),
			        end=gen_time('2014-12-31 15:00:00'),
			        speed=SPEED_REALTIME)
	def testrunner():
		print '.' + str(ticker.now)
		
	ticker.bind(None, testrunner)
	ticker.run()
	print ticker.now
	sleep(3)
	print ticker.now
