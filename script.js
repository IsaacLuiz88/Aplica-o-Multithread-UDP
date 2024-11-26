const chatContainer = document.getElementById('chat-container');
const usernameInput = document.getElementById('username-input');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

let socket;

function conectar() {
    socket = new WebSocket('ws://localhost:8765');

    socket.onopen = () => {
        console.log('Conectado ao servidor');
        addMessage('Sistema', 'Conexão estabelecida!');
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Não mostrar mensagens UDP
        if (data.username !== 'UDP') {
            // Não mostrar a própria mensagem novamente
            if (data.username !== usernameInput.value.trim() && data.username !== 'Anônimo') {
                addMessage(data.username, data.message);
            }
        }
    };

    socket.onerror = (error) => {
        console.error('Erro de WebSocket:', error);
        addMessage('Sistema', 'Erro de conexão');
    };

    socket.onclose = () => {
        addMessage('Sistema', 'Conexão perdida. Reconectando...');
        setTimeout(conectar, 3000);
    };
}

conectar();

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function sendMessage() {
    const username = usernameInput.value.trim() || 'Anônimo';
    const message = messageInput.value.trim();

    if (message && socket.readyState === WebSocket.OPEN) {
        const data = { username, message };
        socket.send(JSON.stringify(data));
        messageInput.value = '';
        addMessage(username, message, true);
    }
}

function addMessage(username, message, isSelf = false) {
    const messageElement = document.createElement('div');
    messageElement.innerHTML = `
        <strong style="color: ${isSelf ? 'green' : 'blue'}">
            ${username}:
        </strong> ${message}
    `;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}