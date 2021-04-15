from flask import Flask, request, jsonify
import logging
import zmq
import queue

app = Flask(__name__)

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect('tcp://localhost:5557')


@app.route('/buy', methods=['POST'])
def send_buy_signal():
    data = request.json  # type(data) is dict
    msg = f"0 {data['username']} {data['usd']}"
    print(f"recieve message: {msg}")
    try:
        socket.send_string(msg)
    except queue.Full:
        print('Task queue is full')
    return 'success', 200


@app.route('/follow_and_dm', methods=['POST'])
def follow_and_dm_signal():
    data = request.json  # type(data) is dict
    msg = f"7 {data['username']}"
    print(f"recieve message: {msg}")
    try:
        socket.send_string(msg)
    except queue.Full:
        print('Task queue is full')
        return 'retry', 404
    return 'success', 200
