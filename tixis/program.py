from tixis import app
from flask import request, render_template, url_for, redirect
#from common.db import DBAgent
from common.db import db
from bson.objectid import ObjectId

class Program(object):
    @staticmethod
    def create(name, desc='', target_type='percent', target_value=0):
        # create the program in db
        oid = db.programs.insert({'name':name, 'desc':desc,
                                     'target_type':target_type,
                                     'target_value':target_value})
        return Program(str(oid))

    @staticmethod
    def list():
        programs = db.programs.find()
        progs = []
        for program in programs:
            progs.insert(Program(str(program._id)))


    def __init__(self, oid='', doc=None):
        if oid:
            prog = db.programs.find_one({'_id':ObjectId(oid)})
            if not prog:
                raise KeyError('No program with this ID found: %s.' % oid)
        self.oid = str(prog['_id'])
        self.name = prog['name']
        self.desc = prog['desc']
        self.target_type = prog['target_type']
        self.target_value = prog['target_value']


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
        prog = Program.create(**new_program)
        return redirect(url_for('program_detail', oid=prog.oid))

@app.route("/program/detail/<oid>")
def program_detail(oid):
    prog = Program(oid)
    return render_template('program_detail.html', prog=prog)

@app.route("/programs/")
def program_list():
    progs = []

    return render_template('program_list.html', progs=progs)


