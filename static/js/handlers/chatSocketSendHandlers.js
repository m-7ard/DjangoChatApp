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
    'manage-friendship': function acceptOrRejectFriendRequestDB(event) {
        let trigger = event.target.closest('[data-command="manage_friendship"]');
        let friendshipPk = trigger.closest('.friendship, .tooltip').dataset.pk;
        let kind = trigger.dataset.kind;
        chatSocket.send(JSON.stringify({
            'action': 'manage_friendship',
            'kind': kind,
            'friendshipPk': friendshipPk,
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
    'delete-backlog': ({objectType, objectPk}) => {
        chatSocket.send(JSON.stringify({
            'action': 'delete-backlog',
            'objectType': objectType,
            'objectPk': objectPk
        }));
    },
    'react': ({objectType, objectPk, emotePk}) => {
        chatSocket.send(JSON.stringify({
            'action': 'react',
            'objectType': objectType,
            'objectPk': objectPk,
            'emotePk': emotePk
        }));
    },
    'edit-message': function editMessageDB({messagePk, content}) {
        chatSocket.send(JSON.stringify({
            'action': 'edit-message',
            'messagePk': messagePk,
            'content': content
        }));
    },
};