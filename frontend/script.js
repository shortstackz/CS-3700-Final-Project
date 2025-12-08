const nodeChoice = prompt("Connect to server A or B? (A/B)") || "A";
const port = nodeChoice.toUpperCase() === "A" ? 5000 : 5001;

const socket = io(`http://localhost:${port}`);

const messagesEl = document.getElementById("messages");
const serverStatus = document.getElementById("serverStatus");
const msgInput = document.getElementById("msgInput");
const sendBtn = document.getElementById("sendBtn");

/* Connection Status */
socket.on("connect", () => {
    serverStatus.textContent = `Connected to Node ${nodeChoice.toUpperCase()}`;
    serverStatus.style.color = "#4caf50";
});

socket.on("disconnect", () => {
    serverStatus.textContent = "Disconnected – trying to reconnect…";
    serverStatus.style.color = "#e53935";
});

/* Receiving messages */
socket.on("message", data => {
    const div = document.createElement("div");
    div.classList.add("msg");
    div.textContent = `${data.user}: ${data.text}`;
    messagesEl.appendChild(div);

    messagesEl.scrollTop = messagesEl.scrollHeight;
});

/* Sending messages */
sendBtn.onclick = sendMessage;
msgInput.addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
});

function sendMessage() {
    const text = msgInput.value.trim();
    if (!text) return;

    socket.emit("send_message", {
        user: "User",
        text
    });

    msgInput.value = "";
}
