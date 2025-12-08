import os
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import redis
import threading
import json
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
SERVER_NAME = os.getenv("SERVER_NAME", "ServerA")

socketio = SocketIO(app, cors_allowed_origins="*", message_queue=f"redis://{REDIS_HOST}:{REDIS_PORT}")

# Redis connections
r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("chat", "users")

# Local tracking
connected_users = {}  # {session_id: username}

def listen_to_redis():
    """Background thread to listen for Redis pub/sub messages"""
    for msg in pubsub.listen():
        if msg["type"] == "message":
            data = json.loads(msg["data"])
            
            if msg["channel"] == "chat":
                # Broadcast chat messages to all connected clients
                socketio.emit("message", data)
            elif msg["channel"] == "users":
                # Broadcast user list updates
                socketio.emit("user_list", data)

threading.Thread(target=listen_to_redis, daemon=True).start()

@app.route("/")
def home():
    return f"WordAround Chat Server ({SERVER_NAME}) Running"

@app.route("/health")
def health():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "server": SERVER_NAME, "users": len(connected_users)}

@socketio.on("connect")
def handle_connect():
    """Handle new client connections"""
    print(f"Client connected: {request.sid} on {SERVER_NAME}")
    emit("server_info", {"server": SERVER_NAME, "sid": request.sid})
    
    # Send message history to new client
    history = get_message_history()
    emit("message_history", history)
    
    # Send current user list
    users = get_all_users()
    emit("user_list", {"users": users})

@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnections"""
    if request.sid in connected_users:
        username = connected_users[request.sid]
        del connected_users[request.sid]
        
        # Update Redis user list
        r.hdel("users", request.sid)
        
        # Broadcast updated user list
        users = get_all_users()
        r.publish("users", json.dumps({"users": users, "action": "leave", "username": username}))
        
        print(f"User {username} disconnected from {SERVER_NAME}")

@socketio.on("join")
def handle_join(data):
    """Handle user joining the chat"""
    username = data.get("username", "Anonymous")
    connected_users[request.sid] = username
    
    # Store user in Redis (shared across all servers)
    r.hset("users", request.sid, username)
    
    # Get updated user list
    users = get_all_users()
    
    # Publish user join event
    r.publish("users", json.dumps({
        "users": users,
        "action": "join",
        "username": username
    }))
    
    # Send system message
    system_msg = {
        "username": "System",
        "message": f"{username} joined the chat",
        "timestamp": datetime.now().isoformat(),
        "server": SERVER_NAME,
        "type": "system"
    }
    r.publish("chat", json.dumps(system_msg))
    
    print(f"User {username} joined on {SERVER_NAME}")

@socketio.on("send_message")
def handle_message(data):
    """Handle incoming chat messages"""
    username = connected_users.get(request.sid, "Anonymous")
    
    message_data = {
        "username": username,
        "message": data.get("message", ""),
        "timestamp": datetime.now().isoformat(),
        "server": SERVER_NAME,
        "type": "user"
    }
    
    # Publish to Redis (all servers will receive this)
    r.publish("chat", json.dumps(message_data))
    
    # Store in message history (keep last 100 messages)
    r.lpush("message_history", json.dumps(message_data))
    r.ltrim("message_history", 0, 99)

def get_message_history(limit=50):
    """Retrieve message history from Redis"""
    history = r.lrange("message_history", 0, limit - 1)
    return [json.loads(msg) for msg in reversed(history)]

def get_all_users():
    """Get all connected users from Redis"""
    user_dict = r.hgetall("users")
    return list(user_dict.values())

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)