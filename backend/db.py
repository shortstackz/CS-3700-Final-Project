from gevent import monkey
monkey.patch_all()

import os
import time
from flask import Flask, request
from flask_socketio import SocketIO, emit
import redis
import json
from datetime import datetime
from db import db as message_db  # Import our database

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
SERVER_NAME = os.getenv("SERVER_NAME", "ServerA")

socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    message_queue=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    async_mode='gevent'
)

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Check if Redis has data, if not restore from DB
try:
    msg_count = r.llen("message_history")
    if msg_count == 0:
        print(f"Redis empty, restoring from database...")
        restored = message_db.sync_to_redis(r)
        print(f"Restored {restored} messages from database")
except redis.RedisError as e:
    print(f"Redis error during startup: {e}")

connected_users = {}

@app.route("/")
def home():
    return f"WordAround Chat Server ({SERVER_NAME}) Running"

@app.route("/health")
def health():
    """Health check endpoint for monitoring"""
    try:
        r.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy", 
        "server": SERVER_NAME, 
        "users": len(connected_users),
        "redis": redis_status,
        "db_messages": len(message_db.get_recent_messages(100))
    }

@socketio.on("connect")
def handle_connect():
    """Handle new client connections"""
    print(f"Client connected: {request.sid} on {SERVER_NAME}")
    emit("server_info", {"server": SERVER_NAME, "sid": request.sid})
    
    # Try Redis first, fall back to database
    try:
        history = get_message_history()
    except redis.RedisError:
        print("Redis unavailable, loading from database")
        history = message_db.get_recent_messages(50)
    
    emit("message_history", history)
    
    users = get_all_users()
    emit("user_list", {"users": users})

@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnections"""
    if request.sid in connected_users:
        username = connected_users[request.sid]
        del connected_users[request.sid]
        
        try:
            r.hdel("users", request.sid)
        except redis.RedisError:
            pass
        
        users = get_all_users()
        socketio.emit("user_list", {
            "users": users, 
            "action": "leave", 
            "username": username
        })
        
        system_msg = {
            "username": "System",
            "message": f"{username} left the chat",
            "timestamp": time.time(),
            "server": SERVER_NAME,
            "type": "system"
        }
        
        # Save to database
        try:
            message_db.save_message(system_msg)
        except Exception as e:
            print(f"Database save error: {e}")
        
        socketio.emit("message", system_msg)
        print(f"User {username} disconnected from {SERVER_NAME}")

@socketio.on("join")
def handle_join(data):
    """Handle user joining the chat"""
    username = data.get("username", "Anonymous")
    connected_users[request.sid] = username
    
    print(f"User {username} (session: {request.sid}) joined on {SERVER_NAME}")
    
    try:
        r.hset("users", request.sid, username)
    except redis.RedisError:
        pass
    
    users = get_all_users()
    
    socketio.emit("user_list", {
        "users": users,
        "action": "join",
        "username": username
    })
    
    system_msg = {
        "username": "System",
        "message": f"{username} joined the chat",
        "timestamp": time.time(),
        "server": SERVER_NAME,
        "type": "system"
    }
    
    # Save to database
    try:
        message_db.save_message(system_msg)
    except Exception as e:
        print(f"Database save error: {e}")
    
    socketio.emit("message", system_msg)

@socketio.on("send_message")
def handle_message(data):
    """Handle incoming chat messages"""
    username = data.get("username") or connected_users.get(request.sid, "Anonymous")
    
    message_data = {
        "username": username,
        "message": data.get("message", ""),
        "timestamp": time.time(),
        "server": SERVER_NAME,
        "type": "user"
    }
    
    print(f"Processing message from {username}: {message_data['message']}")
    
    # Save to database (persistent)
    try:
        message_db.save_message(message_data)
    except Exception as e:
        print(f"Database save error: {e}")
    
    # Save to Redis (fast access)
    try:
        r.lpush("message_history", json.dumps(message_data))
        r.ltrim("message_history", 0, 99)
    except redis.RedisError as e:
        print(f"Redis error: {e}")
    
    socketio.emit("message", message_data)

def get_message_history(limit=50):
    """Retrieve message history from Redis"""
    try:
        history = r.lrange("message_history", 0, limit - 1)
        return [json.loads(msg) for msg in reversed(history)]
    except redis.RedisError:
        # Fallback to database
        return message_db.get_recent_messages(limit)

def get_all_users():
    """Get all connected users from Redis"""
    try:
        user_dict = r.hgetall("users")
        return list(user_dict.values())
    except redis.RedisError:
        # Return local users only
        return list(connected_users.values())

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
