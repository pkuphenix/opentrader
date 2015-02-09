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
    def lt(a, b):
        return a < b

    @staticmethod
    def exist(a):
        return a is not None and a != ""


