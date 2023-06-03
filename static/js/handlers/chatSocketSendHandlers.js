const chatSocketSendHandlers = {
	'ping': function(event) {
        console.log('pinged')
        chatSocket.send(JSON.stringify({
            'action': 'ping'
        }))
    },
	'requestServerResponse': async () => {
        try {
            // send the ping message to the server
            await chatSocket.send(JSON.stringify({
            'action': 'requestServerResponse'
            }));
            console.log('requestServerResponse');
        } catch (error) {
            console.error('Error requestServerResponse', error);
        }
    },
    'manage-friendship': ({friendshipPk, friendPk, kind}) => {
        chatSocket.send(JSON.stringify({
            'action': 'manage-friendship',
            'friendshipPk': friendshipPk,
            'kind': kind,
            'friendPk': friendPk
        }));
    },
    'send-message': function submitMessage(event) {
        if (!(event.key == "Enter") || (event.key === "Enter" && event.shiftKey)) {
            return;
        };
        let chatbarInput = document.querySelector('.chatbar__input');
        event.preventDefault();
        chatSocket.send(JSON.stringify({
            'action': 'send-message',
            'content': chatbarInput.value.trim()
        }));
        chatbarInput.value = '';
    },
};