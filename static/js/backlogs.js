const backlogs = document.getElementById('backlogs');
window.onload = (event) => backlogs.scroll(0, backlogs.scrollHeight);
const chatbar = document.getElementById('chatbar');
chatbar.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        input = event.target;
        event.preventDefault();
        content = input.value;
        input.value = '';
        chatSocket.send(JSON.stringify({
            'action': 'create_message',
            'content': content
        }));
    };
});