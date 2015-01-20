from flask import Flask

app = Flask(__name__)
import program
import trade

@app.route("/")
def hello():
    return "Hello World!"

