// Configuration
const servers = [
    'http://localhost:5000',
    'http://localhost:5001',
    'http://localhost:5002'
];

let currentServerIndex = 0;
let socket;
let username = '';
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// DOM Elements
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');
const messagesDiv = document.getElementById('messages');
const userList = document.getElementById('userList');
const serverStatus = document.getElementById('serverStatus');

// Initialize
function init() {
    // Prompt for username
    while (!username || username.trim() === '') {
        username = prompt('Enter your username:');
        if (username === null) {
            username = 'Anonymous_' + Math.floor(Math.random() * 1000);
            break;
        }
    }
    username = username.trim();
    console.log('Username set to:', username);
    
    connectToServer();
    setupEventListeners();
}

// Connect to a server with fault tolerance
function connectToServer() {
    const serverUrl = servers[currentServerIndex];
    console.log(`Attempting to connect to ${serverUrl}...`);
    
    updateServerStatus('Connecting...', 'connecting');
    
    socket = io(serverUrl, {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 3
    });
    
    // Connection successful
    socket.on('connect', () => {
        console.log('Connected to server');
        updateServerStatus('Connected', 'connected');
        reconnectAttempts = 0;
        
        // Join the chat with username
        console.log('Emitting join event with username:', username);
        socket.emit('join', { username: username });
    });
    
    // Receive server info
    socket.on('server_info', (data) => {
        console.log('Connected to:', data.server);
        updateServerStatus(`Connected to ${data.server}`, 'connected');
    });
    
    // Receive message history
    socket.on('message_history', (history) => {
        console.log('Received message history:', history);
        messagesDiv.innerHTML = ''; // Clear placeholder
        if (history && history.length > 0) {
            history.forEach(msg => displayMessage(msg));
        } else {
            messagesDiv.innerHTML = '<div class="placeholder">No messages yet...</div>';
        }
    });
    
    // Receive new messages
    socket.on('message', (data) => {
        console.log('Received message:', data);
        // Remove placeholder if it exists
        const placeholder = messagesDiv.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        displayMessage(data);
    });
    
    // Update user list
    socket.on('user_list', (data) => {
        console.log('Received user list:', data);
        if (data.users) {
            updateUserList(data.users);
        }
        
        // Show join/leave notifications
        if (data.action === 'join' && data.username !== username) {
            showNotification(`${data.username} joined the chat`);
        } else if (data.action === 'leave') {
            showNotification(`${data.username} left the chat`);
        }
    });
    
    // Connection error
    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        updateServerStatus('Connection Error', 'error');
        tryNextServer();
    });
    
    // Disconnected
    socket.on('disconnect', (reason) => {
        console.log('Disconnected:', reason);
        updateServerStatus('Disconnected', 'disconnected');
        
        if (reason === 'io server disconnect') {
            // Server deliberately disconnected, try next server
            tryNextServer();
        }
        // Otherwise, socket.io will automatically try to reconnect
    });
}

// Try connecting to the next server (fault tolerance)
function tryNextServer() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        updateServerStatus('All servers unavailable', 'error');
        showNotification('Cannot connect to any server. Please refresh the page.');
        return;
    }
    
    reconnectAttempts++;
    currentServerIndex = (currentServerIndex + 1) % servers.length;
    
    console.log(`Trying next server: ${servers[currentServerIndex]}`);
    
    // Disconnect current socket
    if (socket) {
        socket.disconnect();
    }
    
    // Try connecting to next server after a delay
    setTimeout(connectToServer, 2000);
}

// Display a message in the chat
function displayMessage(data) {
    const messageEl = document.createElement('div');
    messageEl.classList.add('message');
    
    if (data.type === 'system') {
        messageEl.classList.add('system-message');
    } else if (data.username === username) {
        messageEl.classList.add('own-message');
    }
    
    const timestamp = new Date(data.timestamp).toLocaleTimeString();
    
    messageEl.innerHTML = `
        <div class="message-header">
            <span class="username">${escapeHtml(data.username)}</span>
            <span class="timestamp">${timestamp}</span>
            <span class="server-badge">${data.server}</span>
        </div>
        <div class="message-content">${escapeHtml(data.message)}</div>
    `;
    
    messagesDiv.appendChild(messageEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Update the user list
function updateUserList(users) {
    console.log('Updating user list with:', users);
    userList.innerHTML = '';
    
    if (!users || users.length === 0) {
        userList.innerHTML = '<li class="no-users">No users online</li>';
        return;
    }
    
    users.forEach(user => {
        const li = document.createElement('li');
        li.textContent = user;
        if (user === username) {
            li.classList.add('current-user');
            li.textContent += ' (you)';
        }
        userList.appendChild(li);
    });
}

// Update server status indicator
function updateServerStatus(text, status) {
    serverStatus.textContent = text;
    serverStatus.className = 'server-indicator ' + status;
}

// Show notification message
function showNotification(text) {
    const notif = document.createElement('div');
    notif.classList.add('notification');
    notif.textContent = text;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}

// Send a message
function sendMessage() {
    const message = msgInput.value.trim();
    
    if (!message) return;
    
    if (!socket || !socket.connected) {
        showNotification('Not connected to server');
        return;
    }
    
    console.log('Sending message:', message);
    socket.emit('send_message', { message: message, username: username });
    msgInput.value = '';
}

// Setup event listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    
    msgInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start the application
init();