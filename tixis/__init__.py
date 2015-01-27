from flask import Flask, request, render_template, url_for, redirect
from agents.xueqiu.sync import XueqiuSyncer

app = Flask(__name__)
import program
import trade

@app.route("/")
def hello():
    return "Hello Worl1d!"

@app.route("/landscape/")
def landscape():
    symbols = XueqiuSyncer().get_normal_symbols()
    return render_template('landscape.html', symbols=symbols)

