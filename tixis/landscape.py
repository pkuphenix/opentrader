from tixis import app
from flask import Flask, request, render_template, url_for, redirect
from core.query import QuerySet
from core.stock import Stock
from urllib import unquote
from common.db import db_ot
import pymongo
from agents.xueqiu.newhigh import *
from datetime import date
from common.utils import gen_date

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

@app.route('/landscape/newhigh', defaults={'today': None})
@app.route("/landscape/newhigh/<today>")
def newhigh(today):
    if today:
        today = gen_date(today)
    else:
        today = date.today()
    display = request.args.get('display', 'graph') # graph or list
    (newlist, repeatlist) = get_newhigh_52w(today)
    stock_dict = {}
    newsymbols = []
    repeatsymbols = []
    for each in newlist:
        newsymbols.append(each['symbol'])
        stock_dict[each['symbol']] = Stock(each['symbol'])
    for each in repeatlist:
        repeatsymbols.append(each['symbol'])
        stock_dict[each['symbol']] = Stock(each['symbol'])
    return render_template('landscape_newhigh.html', newlist=newlist, repeatlist=repeatlist, display=display, date=today, stock_dict=stock_dict, newsymbols=':'.join(newsymbols), repeatsymbols=':'.join(repeatsymbols))
