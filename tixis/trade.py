from tixis import app
from flask import render_template

@app.route("/trade/add/")
def trade_add():
    return render_template('trade_add.html')
