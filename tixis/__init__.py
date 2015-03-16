from flask import Flask, request, render_template, url_for, redirect
from agents.xueqiu.sync import XueqiuSyncer

app = Flask(__name__)
import program
import trade
import landscape
import utils
import session

@app.route("/")
def index():
    return redirect(url_for('program_list'))



