from tixis import app
from flask import request, render_template, url_for, redirect, abort
from bson.objectid import ObjectId
from tixis.model import *
from agents.xueqiu.api import XueqiuAPI

@app.route("/utils/captcha", methods=['POST','GET'])
def captcha_hack():
    a = XueqiuAPI.get_api()
    if request.method == 'GET':
        a.captcha_get('/var/www/test/captcha.jpg')
        return render_template('captcha_hack.html', error_show='hidden')
    elif request.method == 'POST':
        captcha = str(request.form['captcha'])
        e = a.captcha_post(captcha)
        return render_template('captcha_hack.html', error_show='', error_msg=str(e))
