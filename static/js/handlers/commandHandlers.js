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
		let target = formbox.getElementById(targetSelector);
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
    'edit-message': (event) => {
        // Close any open editors
        let messagesWithOpenEditors = document.querySelectorAll('.backlog--editing');
        messagesWithOpenEditors?.forEach((openMessage) => stopEditing(openMessage));

        // Message DOM elements
        let message = event.target.closest('.backlog');
        let messageContent = message.querySelector('.backlog__content');
        let messageBody = message.querySelector('.backlog__body');

        let editInput = quickCreateElement('textarea', {
            classList: ['backlog__edit'],
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


        // Add functionality to prompts
        prompts.querySelector('[data-action="save"]').addEventListener('click', save);
        prompts.querySelector('[data-action="cancel"]').addEventListener('click', () => stopEditing(message));
        
        // Shorcuts
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
                'messagePk': message.dataset.pk, 
            }));
        };
    },
    'react': (event) => {
        let contextObject = event.target.closest('[data-context]');
        let emoteObject = event.target.closest('[data-emote-pk]');
        chatSocket.send(JSON.stringify({
            action: 'react',
            context: contextObject.dataset.context,
            emotePk: emoteObject.dataset.emotePk
        }));
    },
    'emote-to-text': (event) => {
        let trigger = event.target.closest('[data-command="emote-to-text"]');
        let contextObject = event.target.closest('[data-context]');
        let context = JSON.parse(contextObject.dataset.context);
        let inputParent = document.querySelector(context.variables.inputParent);
        let input = inputParent.querySelector('[data-role="input"]');
        input.value += `:${trigger.dataset.name}:`;
    },
    'manage-friendship': (event) => {
        let trigger = event.target.closest('[data-command="manage-friendship"]');
        let contextObject = event.target.closest('[data-context]');
        
        chatSocket.send(JSON.stringify({
            action: 'manage-friendship',
            context: contextObject.dataset.context,
            kind: trigger.dataset.kind,
        }));
    },
    'get-form': async (event) => {
        event.preventDefault();
        let trigger = event.target.closest('[data-command="get-form"]');
        let formString = await getView({name: trigger.dataset.name, kwargs: trigger.dataset.kwargs});
        let form = parseHTML(formString);
        quickCreateElement('div', {
            parent: document.body,
            classList: ['layer'],
            innerHTML: form.outerHTML,
            eventListeners: {
                'mouseup': (e) => {
                    if (e.target.closest('.form__close')) {
                        e.target.closest('.layer').remove();
                    };
                },
            }
        });
    },
    /*
    'get-form': async (event) => {
        event.preventDefault();
        let trigger = event.target.closest('[data-command="get-form"]');
        let target = trigger.dataset.target;
        let contextObject = trigger.closest('[data-context]');
        let url = new URL(window.location.origin + '/GetViewByName/' + target);
        if (contextObject) {
            url.searchParams.append('context', contextObject.dataset.context);
        };
        let request = await fetch(url);
        let response = await request.text();
        let form = parseHTML(response);
        quickCreateElement('div', {
            parent: document.body,
            classList: ['layer'],
            innerHTML: form.outerHTML,
            eventListeners: {
                'mouseup': (e) => {
                    if (e.target.closest('.form__close')) {
                        e.target.closest('.layer').remove();
                    };
                },
            }
        });
    },
    */
};