const commandHandlers = {
	'close-error': (event) => {
		event.target.closest('.error').remove();
	},
	'select-option': (event) => {
		let option = event.target.closest('.option');
		let select = option.closest('.select');
		let selectTrigger = select.querySelector('.select__trigger');
		let triggerName = selectTrigger.querySelector('.option__name');
		triggerName.innerText = option.dataset.value;
		select.classList.remove('select--active');
	},
	'switch-tab': (event) => {
		let button = event.target.closest('[data-command="switch-tab"]');
		let formbox = button.closest('.switchable');
		let targetSelector = button.dataset.target;
		let target = formbox.querySelector(targetSelector);
		formbox.querySelectorAll('.switchable__content').forEach((form) => form.classList.add('switchable__content--hidden'));
		target.classList.remove('switchable__content--hidden');
	},
    'delete-backlog': ({objectType, objectPk}) => {
        chatSocket.send(JSON.stringify({
            'action': 'delete-backlog',
            'objectType': objectType,
            'objectPk': objectPk
        }));
    },
    'edit-message': ({message}) => {
        // Close any open editors
        let messagesWithOpenEditors = document.querySelectorAll('.message--editing');
        messagesWithOpenEditors?.forEach((openMessage) => stopEditing(openMessage));

        // Message DOM elements
        let messageContent = message.querySelector('.backlog__content');
        let messageBody = message.querySelector('.backlog__body');

        let editInput = quickCreateElement('textarea', {
            classList: ['backlog__edit'],
            attributes: {},
            parent: messageContent,
            eventListeners: {'keypress': (e) => {
                if (!(e.key == "Enter") || (e.key === "Enter" && e.shiftKey)) {
                    return;
                };
                save();
            }},
        });

        // Prompts for saving and canceling
        let prompts = quickCreateElement('div', {
            classList: ['backlog__prompts'],
            attributes: {},
            parent: messageBody,
        });
        prompts.innerHTML = `
            <span data-action="cancel">Cancel</span>
            <span data-action="save">Save</span>
        `;

        // Show message as being edited
        message.classList.add('backlog--editing');

        // Put message content into the editor (emotes are converted to text, line breaks converted to \n)
        editInput.value = (Array.from(messageContent.childNodes).reduce((accumulator, current) => {
            if (current.alt) {
                accumulator += ':' + current.alt + ':';
            } 
            else if (current.textContent) {
                accumulator += current.textContent;
            }
            else if (current.nodeName == 'BR') {
                accumulator += '\n'
            };
            return accumulator;
        }, '')).trim(); // remove leading and trailing whitespace


        prompts.querySelector('[data-action="save"]').addEventListener('click', save);
        prompts.querySelector('[data-action="cancel"]').addEventListener('click', () => stopEditing(message));
        
        function stopEditing (messageElement) {
            messageElement.classList.remove('backlog--editing');
            messageElement.querySelector('.backlog__edit').remove();
            messageElement.querySelector('.backlog__prompts').remove();
        };

        function save () {
            stopEditing(message);
            chatSocket.send(JSON.stringify({
                'action': 'edit-message',
                'content': editInput.value,
                'messagePk': message.dataset.objectPk, 
            }));
        };
    },
    'react': ({objectType, objectPk, emotePk}) => {
        chatSocket.send(JSON.stringify({
            'action': 'react',
            'objectType': objectType,
            'objectPk': objectPk,
            'emotePk': emotePk
        }));
    },
    'emote-to-text': ({target, emote}) => {
        target.value += `:${emote.dataset.name}:`;
    },
    'open_profile': ({objectType, objectPk, emotePk}) => {
        undefined
    },
    'manage-friendship': ({friendshipPk, friendPk, kind}) => {
        chatSocketSendHandlers['manage-friendship']({
            friendshipPk: friendshipPk,
            friendPk: friendPk,
            kind: kind
        });
    },
};