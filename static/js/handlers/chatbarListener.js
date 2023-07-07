const chatbarInput = document.getElementById('chatbar-input');
window.addEventListener('keyup', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        let content = chatbarInput.value();
        let context = event.trigger.closest('[data-context]').dataset.context;
        chatSocket.send(JSON.stringify({
            action: 'send-message',
            content: content,
            context: context,
        }));
    }
});