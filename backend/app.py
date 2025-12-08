import os
from flask import Flask
from flask_socketio import SocketIO, emit
import redis
import threading
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379

socketio = SocketIO(app, cors_allowed_origins="*", message_queue=f"redis://{REDIS_HOST}:{REDIS_PORT}")

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("chat")

def listen_to_redis():
    for msg in pubsub.listen():
        if msg["type"] == "message":
            data = json.loads(msg["data"])
            socketio.emit("message", data)

threading.Thread(target=listen_to_redis, daemon=True).start()

@app.route("/")
def home():
    return "WordAround Chat Server Running"

@socketio.on("send_message")
def handle_message(data):
    r.publish("chat", json.dumps(data))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
