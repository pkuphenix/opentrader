from tixis import app
from flask import Flask, request, render_template, url_for, redirect
from core.query import QuerySet
from urllib import unquote

@app.route("/landscape/")
def landscape():
    script = request.args.get('script', None)
    #if script is not None:
    #    script = unquote(script)
    display = request.args.get('display', 'graph') # graph or list
    if not script:
        stocks = QuerySet.all().stocks
    else:
        stocks = QuerySet.all().run_script(script).stocks
    return render_template('landscape.html', stocks=stocks, display=display, script=script)