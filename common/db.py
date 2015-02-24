from pymongo import MongoClient
db_ot = MongoClient().opentrader
db_tixis = MongoClient().opentrader_tixis

def drop_dup_k_day():
    sh001 = db_ot.find({'symbol':'SH000001'})
    times = []
    for each in sh001:
        times.append(each['time'])
    
