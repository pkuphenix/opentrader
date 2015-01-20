from datetime import datetime

# str_time: "2010-06-04 21:08:12"
def gen_time(str_time):
    return datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S")

def gen_tick(str_time, precision=1):
    return 