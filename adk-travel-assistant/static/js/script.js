document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, true);
        userInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: message }),
            });

            const data = await response.json();
            console.log('Backend response:', data); // Debugging line
            // Handle structured backend response
            if (data.code === "SUCCESS" && data.data) {
                addMessage(data.data);
            } else if (data.message) {
                let msg = data.message;
                if (data.suggestion) {
                    msg += ' (' + data.suggestion + ')';
                }
                addMessage(msg);
            } else {
                addMessage('Sorry, there was an error processing your request.');
            }
        } catch (error) {
            addMessage('Sorry, there was an error processing your request.');
            console.error('Error:', error);
        }
    }

    // Event Listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Add welcome message
    addMessage('Welcome to the AI Travel Assistant! How can I help you today?');
}); 