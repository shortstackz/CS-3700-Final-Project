from gevent import monkey
monkey.patch_all()

import os
import time
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import redis
import json
from datetime import datetime
from server_sync import ServerSync  # Import sync module

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
SERVER_NAME = os.getenv("SERVER_NAME", "ServerA")

# Get other server URLs from environment
OTHER_SERVERS = os.getenv("OTHER_SERVERS", "").split(",")
OTHER_SERVERS = [s.strip() for s in OTHER_SERVERS if s.strip()]

socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    message_queue=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    async_mode='gevent'
)


r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Initialize server synchronization
if OTHER_SERVERS:
    sync_manager = ServerSync(SERVER_NAME, OTHER_SERVERS)
    sync_manager.start_periodic_sync()
    print(f"Server sync enabled with: {OTHER_SERVERS}")
else:
    sync_manager = None
    print("No other servers configured for sync")

connected_users = {}

@app.route("/")
def home():
    return f"WordAround Chat Server ({SERVER_NAME}) Running"

@app.route("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "server": SERVER_NAME, 
        "users": len(connected_users)
    }

# NEW: REST API for server-to-server sync
@app.route("/api/sync", methods=["GET"])
def sync_endpoint():
    """Endpoint for other servers to request sync data"""
    requesting_server = request.args.get("requesting_server", "unknown")
    print(f"Sync request from {requesting_server}")
    
    try:
        message_count = r.llen("message_history")
        user_list = get_all_users()
        
        return jsonify({
            "server": SERVER_NAME,
            "timestamp": time.time(),
            "users": len(user_list),
            "user_list": user_list,
            "messages": message_count,
            "status": "healthy"
        })
    except Exception as e:
        return jsonify({
            "server": SERVER_NAME,
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/api/event", methods=["POST"])
def event_endpoint():
    """Receive event notifications from other servers"""
    data = request.json
    source = data.get("source_server")
    event_type = data.get("event_type")
    event_data = data.get("data")
    
    print(f"Received {event_type} event from {source}: {event_data}")
    
    # You can add custom logic here to handle events
    # For now, just log them
    
    return jsonify({"status": "received"})

# Rest of your existing code...
@socketio.on("connect")
def handle_connect():
    """Handle new client connections"""
    print(f"Client connected: {request.sid} on {SERVER_NAME}")
    emit("server_info", {"server": SERVER_NAME, "sid": request.sid})


    history = get_message_history()
    emit("message_history", history)
    

    users = get_all_users()
    emit("user_list", {"users": users})

@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnections"""
    if request.sid in connected_users:
        username = connected_users[request.sid]
        del connected_users[request.sid]


        r.hdel("users", request.sid)
        
        # Notify peer servers
        if sync_manager:
            sync_manager.notify_peers("user_leave", {"username": username})
        
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
        socketio.emit("message", system_msg)
        
        print(f"User {username} disconnected from {SERVER_NAME}")

@socketio.on("join")
def handle_join(data):
    """Handle user joining the chat"""
    username = data.get("username", "Anonymous")
    connected_users[request.sid] = username
    
    print(f"User {username} (session: {request.sid}) joined on {SERVER_NAME}")
    

    r.hset("users", request.sid, username)
    
    # Notify peer servers
    if sync_manager:
        sync_manager.notify_peers("user_join", {"username": username})
    
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
    

    r.lpush("message_history", json.dumps(message_data))
    r.ltrim("message_history", 0, 99)
    

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