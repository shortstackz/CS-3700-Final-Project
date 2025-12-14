# WordAround – Real-Time Distributed Chat Application

## Team Members
- **Kalia Chongtoua** – kchongto@msudenver.edu  
- **Jorge Medrano** – jmedra15@msudenver.edu  
- **Mohamed Abdin** – mabdin@msudenver.edu  

---

## Project Overview
**WordAround** is a distributed real-time chat application inspired by popular messaging apps such as WhatsApp, KakaoTalk, and WeChat. The goal of this project is to create a system where multiple users can communicate seamlessly across interconnected servers, demonstrating scalability, concurrency, and fault tolerance in real-time messaging.

Traditional centralized chat systems often suffer from bottlenecks or single points of failure. WordAround addresses this by distributing the messaging workload across multiple servers, ensuring reliability and consistent message delivery even if one server goes offline.

Each server instance:
Accepts WebSocket connections from clients
Shares messages and events via Redis
Periodically synchronizes health and state with peer servers
---

## Problem Statement
Centralized messaging apps face challenges like:

- Performance bottlenecks during high traffic
- Single points of failure
- Limited scalability

This project aims to **design and implement a distributed chat system** that supports multiple simultaneous users, ensures reliable message delivery, and maintains server synchronization to handle fault tolerance and concurrency.

---

## Project Objectives
- Develop a networked chat system supporting **bi-directional communication** between multiple users  
- Enable **communication between distributed servers** using WebSockets  
- Implement **basic fault tolerance**: clients can reconnect to another server if one fails  
- Demonstrate **concurrency handling** for messages across multiple nodes  
- Build a **user-friendly interface** to visualize real-time message synchronization  
- Deliver a working prototype by the end of the semester, with potential for portfolio expansion  

---
## Core Components

- Flask + Socket.IO: Handles HTTP endpoints and real-time WebSocket communication
- Redis:
- Message queue for Socket.IO event propagation
- Shared storage for users and message history
- ServerSync module:
- Periodic peer-to-peer health synchronization
- Best-effort event notifications between servers
- Docker Compose:
- Orchestrates Redis and multiple backend server containers


---

## System Overview / Proposed Solution
The WordAround system consists of:

1. **Chat Servers (Nodes)**  
   - Each server runs a Flask-SocketIO application, either on separate hosts or inside Docker containers  
   - Servers maintain user lists and message histories and periodically synchronize with each other  

2. **Clients**  
   - Clients connect to the nearest chat server via WebSocket  
   - Messages sent by clients are broadcast across the server network to ensure consistency  

3. **Server Synchronization**  
   - Servers exchange updates through REST or WebSocket connections  
   - TCP ensures real-time updates, replication, and fault tolerance  

4. **Implementation Details**  
   - Python + Flask-SocketIO handle real-time message delivery  
   - Docker containers simulate distributed environments and isolate servers for easier testing  
   - The combination of WebSocket communication and containerized nodes provides a realistic distributed system framework  

---
## Simple Diagram

**Clients**
- │
- ▼
- Flask-SocketIO Servers (A, B, C, ...)
- │ │ │
- └────────┴────────┘
Redis
(shared state + message queue)

---

## System Overview -Continued
- Chat Server (backend/app.py)
Each server instance is identical and differentiated only by environment variables.

**Responsibilities:**

- Manage client WebSocket connections
- Broadcast chat messages
- Maintain a shared user list
- Persist recent message history
- Expose REST endpoints for server-to-server coordination

## WebSocket Events
- **Event**	    |     **Direction**	 |    **Description**
- **connect**	      Client → Server	Client establishes connection
- **join**	         Client → Server	User joins chat
- **send_message**   Client → Server	Broadcast chat message
- **disconnect**	   Client → Server	Cleanup on disconnect
- **message**	      Server → Client	Chat message broadcast
- **user_list**	   Server → Client	Updated list of active users
- **message_history**   Server → Client	Recent message history
- **server_info**	   Server → Client	Server identity and session info



---

## Technologies & Tools
- **Language:** Python  
- **Framework:** Flask + Flask-SocketIO  
- **Networking:** WebSocket (SocketIO)  
- **Version Control:** GitHub  
- **Project Management:** Microsoft Teams  
- **Testing Environment:** Flask Virtual Server, SEED Ubuntu (for isolated containers)  

---

## Expected Outcomes
- A **working distributed chat application** enabling multiple users to exchange messages in real-time across interconnected servers  
- **Fault tolerance:** clients automatically reconnect to available servers if one fails  
- **Server synchronization:** all chat rooms remain consistent across multiple nodes  
- A **simple, intuitive interface** for user interaction  
- **WebSocket-based communication** for real-time message delivery and server synchronization  
- Comparable functionality to popular messaging apps (on a smaller scale)
   
---

## Limitations & Future Work
   - No authentication or authorization
   - No message persistence beyond Redis lifetime
   - No conflict resolution for concurrent events
   - No dynamic peer discovery
- **Potential extensions:**
   - JWT-based authentication
   - Persistent storage backend
   - Leader election or consensus
   - Metrics and tracing integration
--- 
## Status 
This backend is production-structured but experimental in guarantees. It is well-suited for coursework, prototypes, and systems demonstrations involving distributed real-time communication.
