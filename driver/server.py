from flask import Flask, request, jsonify
import logging
import zmq
import queue

app = Flask(__name__)

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect('tcp://localhost:5557')


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello, World!'

@app.route('/', methods=['POST'])
def send_signal():
    data = request.json  # type(data) is dict
    request_type = data['type']
    if request_type == 'buy':
        msg = f"0 {data['username']} {data['usd']}"
        print(f"recieve message: {msg}")
        try:
            socket.send_string(msg)
        except Exception as e:
            return jsonify({"code": 404, "msg": e})
        return jsonify({"code": 200, "msg": "buy success"})
    elif request_type == 'follow_and_dm':
        msg = f"7 {data['username']}"
        print(f"recieve message: {msg}")
        try:
            socket.send_string(msg)
        except Exception as e:
            return jsonify({"code": 404, "msg": e})
        return jsonify({"code": 200, "msg": "follow_and_dm success"})
