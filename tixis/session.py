#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, session, redirect, url_for, escape, request, abort
from opentrader.tixis import app
import hashlib
from opentrader.tixis.model import *

def encrypt(data):
    return hashlib.sha224(data).hexdigest()

class Account(TixisModel):
    _collection_name = 'account'
    _fields = [
        CharField(name="username", unique=True, optional=False),
        CharField(name="password", optional=False),
        CharField(name="email"),
    ]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = Account.find_one({'username':request.form['username']})
        if not account:
            abort(404)
        if encrypt(request.form['password']) == account.password:
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    return '''
        <form action="" method="post">
            <p>用户名&nbsp;<input type="text" name="username" /></p>
            <p>密码&nbsp;<input type="password" name="password" /></p>
            <p><input type="submit" value="Login" /><a href="register">注册</a></p>
        </form>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not request.form['username'] or not request.form['password']:
            return 'Empty username or password.'
        existing = Account.find_one({'username':request.form['username']})
        if existing:
            return 'The user already exists.'
        username = request.form['username']
        password = encrypt(request.form['password'])
        email = request.form['email']
        Account.new(username=username, password=password, email=email)
        session['username'] = username
        return redirect(url_for('index'))
    return '''
        注册：
        <form action="" method="post">
            <p>用户名&nbsp;<input type="text" name="username" /></p>
            <p>密码&nbsp;<input type="password" name="password" /></p>
            <p>email&nbsp;<input type="text" name="email" /></p>
            <p><input type="submit" value="提交注册" /></p>
        </form>
    '''

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

app.secret_key = '\xf6:R\x9c#\xdbf\xb3\x9a\x02\xb6\xaf\xe8\xf0\xd1\xc0\xa5\xb8o\x9ej2\xa6\x87'

def getuser():
    if 'username' in session:
        return escape(session['username'])
    else:
        return None

