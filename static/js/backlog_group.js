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
const chatbarTextInput = document.getElementById('chatbar-text-input');
const chatbarFileInput = document.getElementById('chatbar-file-input');
chatbar.addEventListener('keydown', async (event) => {
    if (mentionableObserver.activeMentionable) {
        return;
    };

    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        content = chatbarTextInput.value.trim();
        file = chatbarFileInput.files[0];
        if (!content || !file) {
            return;
        };


        const sendData = {
            'content': content
        };

        const fileReader = new FileReader();
        fileReader.onload = (event) => {
            const dataUrl = event.target.result;
            const [_, base64] = dataUrl.split(','); 

            sendData.file = {
                'base64': base64,
                'name': file.name,
            }
            
            chatbarTextInput.value = '';
            chatbarFileInput.value = '';

            chatSocket.send(JSON.stringify({
                'action': 'create_message',
                ...sendData
            }));
        };
    
        fileReader.readAsDataURL(file);
    };
});