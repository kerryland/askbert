from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route('/ask')
def ask():
    response = jsonify(
            {
                "message": request.args.get('q', '')
            }
    )
    return response

