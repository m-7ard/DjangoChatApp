const backlogs = document.getElementById('backlogs');
window.onload = (event) => {
    backlogs.addEventListener('scroll', () => {
        if (!(backlogs.scrollTop === 0)) {
            return;
        };
 
        chatSocket.send(JSON.stringify({
            'action': 'generate_backlogs',
        }));
    });
};
const chatbar = document.getElementById('chatbar');
const chatbarInput = chatbar.querySelector('[data-role="input"]');
chatbar.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        input = event.target;
        event.preventDefault();
        content = input.value.trim();
        if (!content) {
            return;
        };
        input.value = '';
        chatSocket.send(JSON.stringify({
            'action': 'create_message',
            'content': content
        }));
    };
});