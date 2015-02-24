from datetime import datetime

# str_time: "2010-06-04 21:08:12"
def gen_time(str_time):
    return datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")

def gen_tick(str_time, precision=1):
    return 


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
            
