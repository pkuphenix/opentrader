from tixis import app
from flask import Flask, request, render_template, url_for, redirect
from core.query import QuerySet
from core.stock import Stock
from urllib import unquote
from common.db import db_ot
import pymongo

@app.route("/landscape/")
def landscape():
    script = request.args.get('script', '')
    #if script is not None:
    #    script = unquote(script)
    display = request.args.get('display', 'graph') # graph or list
    if not script:
        stocks = QuerySet.all().stocks
    else:
        stocks = QuerySet.all().run_script(script).stocks
    return render_template('landscape_overview.html', stocks=stocks, display=display, script=script)

@app.route("/landscape/newhigh")
def newhigh():
    display = request.args.get('display', 'graph') # graph or list
    limit = request.args.get('limit', '10')
    records = list(db_ot.policy_newhigh.find().sort('time', pymongo.DESCENDING).limit(int(limit)))
    records.reverse()
    stock_dict = {}
    last_symbol_list = []
    for each_record in records:
        brand_new_symbol_list = []
        repeat_new_symbol_list = []
        for each_symbol in each_record['symbols']:
            if each_symbol not in stock_dict:
                # totally new stock
                stock_dict[each_symbol] = Stock(each_symbol)
                brand_new_symbol_list.append(each_symbol)
            elif each_symbol not in last_symbol_list:
                # not totally new, but not in last list
                repeat_new_symbol_list.append(each_symbol)
        last_symbol_list = each_record['symbols']
        each_record['brand_new'] = brand_new_symbol_list
        each_record['repeat_new'] = repeat_new_symbol_list
    records.reverse()
    return render_template('landscape_newhigh.html', records=records, display=display, stock_dict=stock_dict, symbols=':'.join(stock_dict.keys()))
