from gevent import monkey
monkey.patch_all()

import os
from flask import Flask, request
from flask_socketio import SocketIO, emit
import redis
import json
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
SERVER_NAME = os.getenv("SERVER_NAME", "ServerA")

# SocketIO with Redis message queue handles message distribution automatically
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    message_queue=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    async_mode='gevent'
)

# Redis connection for data storage only (not pub/sub)
r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Local tracking
connected_users = {}  # {session_id: username}

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
        socketio.emit("user_list", {
            "users": users, 
            "action": "leave", 
            "username": username
        })
        
        # Send system message
        system_msg = {
            "username": "System",
            "message": f"{username} left the chat",
            "timestamp": datetime.now().isoformat(),
            "server": SERVER_NAME,
            "type": "system"
        }
        socketio.emit("message", system_msg)
        
        print(f"User {username} disconnected from {SERVER_NAME}")

@socketio.on("join")
def handle_join(data):
    """Handle user joining the chat"""
    username = data.get("username", "Anonymous")
    connected_users[request.sid] = username
    
    print(f"User {username} (session: {request.sid}) joined on {SERVER_NAME}")
    
    # Store user in Redis (shared across all servers)
    r.hset("users", request.sid, username)
    
    # Get updated user list
    users = get_all_users()
    
    print(f"Current user list: {users}")
    
    # Broadcast user list update
    socketio.emit("user_list", {
        "users": users,
        "action": "join",
        "username": username
    })
    
    # Send system message
    system_msg = {
        "username": "System",
        "message": f"{username} joined the chat",
        "timestamp": datetime.now().isoformat(),
        "server": SERVER_NAME,
        "type": "system"
    }
    socketio.emit("message", system_msg)

@socketio.on("send_message")
def handle_message(data):
    """Handle incoming chat messages"""
    # Try to get username from the message data first, then fall back to connected_users
    username = data.get("username") or connected_users.get(request.sid, "Anonymous")
    
    message_data = {
        "username": username,
        "message": data.get("message", ""),
        "timestamp": datetime.now().isoformat(),
        "server": SERVER_NAME,
        "type": "user"
    }
    
    print(f"Processing message from {username}: {message_data['message']}")
    
    # Store in message history
    r.lpush("message_history", json.dumps(message_data))
    r.ltrim("message_history", 0, 99)
    
    # Broadcast to all clients (Redis message_queue handles distribution)
    socketio.emit("message", message_data)

def get_message_history(limit=50):
    """Retrieve message history from Redis"""
    history = r.lrange("message_history", 0, limit - 1)
    return [json.loads(msg) for msg in reversed(history)]

def get_all_users():
    """Get all connected users from Redis"""
    user_dict = r.hgetall("users")
    return list(user_dict.values())

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)