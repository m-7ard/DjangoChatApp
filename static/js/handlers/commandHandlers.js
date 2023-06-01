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
    'delete-backlog': (event) => {
        let backlog = event.target.closest('.backlog');
        let objectType = backlog.dataset.objectType;
        let objectPk = backlog.dataset.pk;

        chatSocketSendHandlers['delete-backlog']({
            'objectType': objectType,
            'objectPk': objectPk,
        });
    },
    'edit-message': (event) => {
        // Close any open editors
        let messagesWithOpenEditors = document.querySelectorAll('.message--editing');
        messagesWithOpenEditors?.forEach((message) => stopEditing(message));

        // Message DOM elements
        let message = event.target.closest('.message');
        let messageContent = message.querySelector('.message__content');
        let messageBody = message.querySelector('.message__body');

        let editInput = quickCreateElement('textarea', {
            classList: ['message__edit'],
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
            classList: ['message__prompts'],
            attributes: {},
            parent: messageBody,
        });
        prompts.innerHTML = `
            <span data-action="cancel">Cancel</span>
            <span data-action="save">Save</span>
        `;

        // Show message as being edited
        message.classList.add('message--editing');

        // Put message content into the editor (emotes are converted to text)
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
            messageElement.classList.remove('message--editing');
            messageElement.querySelector('.message__edit').remove();
            messageElement.querySelector('.message__prompts').remove();
        };

        function save () {
            stopEditing(message);
            chatSocketSendHandlers['edit-message']({
                'content': editInput.value,
                'messagePk': message.dataset.pk, 
            });
        };
    },
    'react': (event) => {
        let emote = event.target.closest('.reaction');
        let object = event.target.closest('[data-object-type]');
        processReaction({
            object: object,
            emote: emote
        });
    },
    'emote-to-text': ({target, emote}) => {
        target.value += `:${emote.dataset.name}:`;
    },
    'open_profile': () => {
        
    },
    'manage-friendship': (event) => {
        let friendship = event.target.closest('[data-object-type="friendship"]');
        let friend = event.target.closest('[data-object-type="friend"]');
        let trigger = event.target.closest('[data-command="manage-friendship"]');

        let friendshipPk = friendship.dataset.objectPk;
        let friendPk = friend.dataset.objectPk;
        let kind = trigger.dataset.kind;
        chatSocketSendHandlers['manage-friendship']({
            friendshipPk: friendshipPk,
            friendPk: friendPk,
            kind: kind
        });
    },
};