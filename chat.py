#!/usr/bin/env python
# Copyright 2013 Abram Hindle
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You can start this by executing it in python:
# python server.py
#
# remember to:
#     pip install flask

# Shared Chat 
#   for each message in
#      for each client
#         send message

import flask
from flask import Flask, request
from flask_sockets import Sockets
import gevent
from gevent import queue  #like async method in the same thread
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)  #wrap the Flask app in a socket app
app.debug = True

clients = list()  #make myself a list of client

def send_all(msg):
    # for each client I will put the message into the message queue
    for client in clients:
        client.put( msg )

def send_all_json(obj):
    send_all( json.dumps(obj) )

class Client:
    def __init__(self):
        self.queue = queue.Queue()
    # this queue is a blocking queue, it doesn't block when we add things to it, but it does when we get things
    def put(self, v):
        self.queue.put_nowait(v)  # add message to the queue

    def get(self):
        return self.queue.get()  #get a message from th queue


@app.route('/') #base route serves the base webpage
def hello():
    return flask.redirect("/static/chat.html")

# 2 threads: reading and writing
def read_ws(ws,client):
    '''A greenlet function that reads from the websocket'''
    # greenlet that runs concurrently with subscribe_socket thread
    try:
        while True: # forever
            msg = ws.receive()
            print "WS RECV: %s" % msg
            if (msg is not None):
                #json parse it if it is a real message
                packet = json.loads(msg)
                send_all_json( packet )
            else:
                break
    except:
        '''Done'''

@sockets.route('/subscribe') # when we call /subscribe, this will start the websocket
def subscribe_socket(ws):
    # greenlet as well, and runs concurrently depends on how many connections you have
    client = Client()
    clients.append(client)
    g = gevent.spawn( read_ws, ws, client )    
    try:
        while True: # sits and waits on the client for it to yield
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print "WS Error %s" % e
    finally:
        clients.remove(client)
        gevent.kill(g)

if __name__ == "__main__":
    # cheap hack
    os.system("bash run.sh");

