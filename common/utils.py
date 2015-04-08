from datetime import datetime
import time

# str_time: "2010-06-04 21:08:12"
def gen_time(str_time):
    return datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")

def standarlize_time(str_time):
    if str_time is None:
        return None
    if type(str_time) in (str, unicode):
        return datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")
    else:
        assert type(str_time) is datetime
        return str_time

def gen_date(str_date):
    return datetime.strptime(str_date, "%Y-%m-%d").date()

# str_time: "2010-06-04 21:08:12" or datetime
def gen_tick(str_time, precision=1):
    if type(str_time) is datetime:
        str_time = str_time.strftime("%Y-%m-%d %H:%M:%S")
    return int(time.mktime(time.strptime(str_time, "%Y-%m-%d %H:%M:%S")) * precision)

class Operator(object):
    @staticmethod
    def gt(a, b):
        return a > b

    @staticmethod
    def gte(a, b):
        return a >= b

    @staticmethod
    def lt(a, b):
        return a < b

    @staticmethod
    def lte(a, b):
        return a <= b

    @staticmethod
    def exist(a):
        return a is not None and a != ""

    @staticmethod
    def inn(a, b):
        if type(b) is list:
            return a in b
        else:
            return a in b.split(':')

class Event(object):
    def __init__(self, source, name):
        self.source = source
        self.name = name

class Observable(object):
    def initob(self):
        self.callbacks = {} # {[]}

    def subscribe(self, name, callback):
        if name not in self.callbacks:
            self.callbacks[name] = []
        self.callbacks[name].append(callback)

    def fire(self, name, **attrs):
        e = Event(self, name)
        for k, v in attrs.iteritems():
            setattr(e, k, v)
        if name in self.callbacks:
            for fn in self.callbacks[name]:
                fn(e)

    def callback_count(self, name):
        if name not in self.callbacks:
            return 0
        else:
            return len(self.callbacks[name])
            
class AntiDupPool(object):
    def __init__(self, size):
        self.size = size
        # initialize a ring queue
        self.rq = {'next':None, 'objs':None}
        p = self.rq
        for i in range(self.size-1):
            p['next'] = {'next':None, 'objs':None}
            p = p['next']
        p['next'] = self.rq
        # initialize a hash
        self.hash = {}

    def filter(self, src):
        # src must be a list
        assert type(src) is list
        # first filter out the result
        res = []
        for each in src:
            if each in self.hash:
                self.hash[each] += 1
            else:
                res.append(each)
                self.hash[each] = 1

        # then reset the ring queue
        if self.rq['objs']:
            for each in self.rq['objs']:
                self.hash[each] -= 1
                if self.hash[each] == 0:
                    del self.hash[each]
        self.rq['objs'] = src
        self.rq = self.rq['next']

        return res

def test_AntiDupPool():
    t = AntiDupPool(3)
    assert t.filter([1,2,3]) == [1,2,3]
    assert t.filter([2,3,4]) == [4]
    assert t.filter([3,4,5]) == [5]
    assert t.filter([4,5,6]) == [6] # overwrites [1,2,3]
    assert t.filter([1,3,4,5,6,7]) == [1,7] # overwrites [2,3,4]
    assert t.filter([1,2,7,8]) == [2,8]


