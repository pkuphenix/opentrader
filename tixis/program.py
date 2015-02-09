from tixis import app
from flask import request, render_template, url_for, redirect, abort
from bson.objectid import ObjectId
from tixis.model import *

class Program(TixisModel):
    _collection_name = 'programs'
    _fields = [
        CharField(name="name", unique=True),
        CharField(name="desc"),
        EnumField(name="target_type", values=('percent', 'amount')),
        UIntField(name="target_value"),
    ]


@app.route("/program/add", methods=['POST','GET'])
def program_add():
    if request.method == 'GET':
        return render_template('program_add.html', error_show='hidden')
    elif request.method == 'POST':
        new_program = {
            'name': request.form['program_name'],
            'desc': request.form['program_desc'],
            'target_type': request.form['target_type'],
            'target_value': request.form['target_value'] or 0,
        }
        try:
            prog = Program.new(**new_program)
        except ValidationError, e:
            return render_template('program_add.html', error_show='', error_msg=str(e))
        return redirect(url_for('program_detail', oid=prog.oid))

@app.route("/program/detail/<oid>")
def program_detail(oid):
    try:
        prog = Program(oid)
    except KeyError:
        abort(404)
    return render_template('program_detail.html', prog=prog)

@app.route("/programs/")
def program_list():
    progs = Program.list()
    return render_template('program_list.html', progs=progs)


