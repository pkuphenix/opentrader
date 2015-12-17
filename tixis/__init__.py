from flask import Flask, request, render_template, url_for, redirect
from opentrader.agents.xueqiu.sync import XueqiuSyncer
from opentrader.core.ticker import RT

app = Flask(__name__)
import opentrader.tixis.program
import opentrader.tixis.trade
import opentrader.tixis.landscape
import opentrader.tixis.utils
import opentrader.tixis.session

@app.route("/")
def index():
    return redirect(url_for('program_list'))

@app.context_processor
def utility_processor():
    return dict(RT=RT)
