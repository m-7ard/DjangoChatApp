const commandHandlers = {
	'close-error': ({trigger, event}) => {
		event.target.closest('.error').remove();
	},
	'select-option': ({trigger, event}) => {
        let option = trigger.querySelector('[data-role="option"]');
        let select = trigger.closest('[data-role="select"]');
        let rootOption = select.querySelector('[data-role="root-option"]');
        rootOption.textContent = option.innerText;
	},
	'switch-content': ({trigger, event}) => {
        let navigation = trigger.closest('.switchable__navigation')
		navigation.querySelectorAll('[data-command="switch-content"]').forEach((contentSwitch) => {
            contentSwitch.dataset.state = 'inactive';
        });
        trigger.dataset.state = 'active';
        
        let target = document.getElementById(trigger.dataset.target);
		let container = trigger.closest('.switchable');
        
        container.querySelectorAll('.switchable__content').forEach((content) => {
            if (content.closest('.switchable') == container) {
                content.classList.remove('switchable__content--active')
            };
        });
        target.classList.add('switchable__content--active');
	},
    'delete-backlog': ({objectType, objectPk}) => {
        chatSocket.send(JSON.stringify({
            'action': 'delete-backlog',
            'objectType': objectType,
            'objectPk': objectPk
        }));
    },
    'edit-message': ({trigger, event}) => {
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
    'react': ({trigger, event}) => {
        let contextObject = event.target.closest('[data-context]');
        let emoteObject = event.target.closest('[data-emote-pk]');
        chatSocket.send(JSON.stringify({
            action: 'react',
            context: contextObject.dataset.context,
            emotePk: emoteObject.dataset.emotePk
        }));
    },
    'emote-to-text': ({trigger, event}) => {
        let contextObject = event.target.closest('[data-context]');
        let context = JSON.parse(contextObject.dataset.context);
        let inputParent = document.querySelector(context.variables.inputParent);
        let input = inputParent.querySelector('[data-role="input"]');
        input.value += `:${trigger.dataset.name}:`;
    },
    'manage-friendship': ({trigger, event}) => {
        let contextObject = event.target.closest('[data-context]');
        
        chatSocket.send(JSON.stringify({
            action: 'manage-friendship',
            context: contextObject.dataset.context,
            kind: trigger.dataset.kind,
        }));
    },
    'get-form': async ({trigger, event}) => {
        event.preventDefault();
        let formString = await getView({
            name: trigger.dataset.name, 
            kwargs: trigger.dataset.kwargs,
            query: trigger.dataset.query,
        });
        let layer = quickCreateElement('div', {
            parent: document.body,
            classList: ['layer', 'layer--form'],
            innerHTML: formString,
            eventListeners: {
                'submit': processForm,
            }
        });
    },
    'get-overlay': async ({trigger, event}) => {
        event.preventDefault();
        let overlayString = await getView({
            name: trigger.dataset.name, 
            kwargs: trigger.dataset.kwargs,
            query: trigger.dataset.query,
        });
        let layer = quickCreateElement('div', {
            parent: document.body,
            classList: ['layer', 'layer--overlay'],
            innerHTML: overlayString,
        });
    },
    'remove-closest': ({trigger, event}) => {
        let targetSelector = trigger.dataset.target;
        let target = trigger.closest(targetSelector);
        target.remove();
    },
    'toggle-sidebar': ({trigger, event}) => {
        let sidebar = document.getElementById(trigger.dataset.target);
        let currentState = sidebar.dataset.state;
        let newState = (currentState == 'closed') ? 'open' : 'closed';
        sidebar.dataset.state = newState;
        trigger.dataset.state = newState;
    },
    'accept_friendship': ({trigger, event, command}) => {
        let friend = trigger.closest('.user');
        let [_, pk] = friend.id.split('-');
        chatSocket.send(JSON.stringify({
            'action': command,
            'pk': pk,
        }));
    },
    'delete_friendship': ({trigger, event, command}) => {
        let friend = trigger.closest('.user');
        let [_, pk] = friend.id.split('-');
        chatSocket.send(JSON.stringify({
            'action': command,
            'pk': pk,
        }));
    }
};