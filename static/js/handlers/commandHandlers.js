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
    'get_overlay': async ({trigger, event}) => {
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
        
        layer.addEventListener('mouseup', (event) => {
            if (event.target.matches('.layer--overlay') || event.target.closest('[data-role="close"]')) {
                layer.remove();
            };
        });
    },
    'get_tooltip': async ({trigger, event, command}) => {
        let tooltip = quickCreateElement('div', {
            classList: ['tooltip'],
            innerHTML: await getView({
                name: trigger.dataset.name,
                kwargs: trigger.dataset.kwargs,
                query: trigger.dataset.query,
            }),
        });
        tooltipManager.toggleTooltip({
            trigger: trigger, 
            tooltip: tooltip, 
            reference: trigger
        });
        tooltip.querySelector('[data-role="close"]')?.addEventListener('click', (event) => tooltipManager.deregisterActiveTooltip());
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
    },
    'select-text': ({trigger, event}) => {
        // Just selects the text in an input
        // used in invite creation menu / tooltip
        let target = document.getElementById(trigger.dataset.target);
        target.select();
    },
    'mark_as_read': ({trigger, event, command}) => {
        chatSocket.send(JSON.stringify({
            'action': command,
        }));
    },
    'delete_backlog': ({trigger, event, command}) => {
        let backlog = trigger.closest('.backlog');
        chatSocket.send(JSON.stringify({
            'action': command,
            'pk': backlog.dataset.pk
        }));
    },
    'edit_message': ({trigger, event, command}) => {
        function save() {
            if (mentionableObserver.activeMentionable) {
                return;
            };

            let editorInput = editor.querySelector('[data-role="input"]');
            content = editorInput.value.trim();
            if (!content) {
                return;
            };
            chatSocket.send(JSON.stringify({
                'action': command,
                'pk': backlog.dataset.pk,
                'content': content,
            }));
            editor.remove();
        };

        document.querySelectorAll('.backlog__editor')?.forEach((openEditor) => openEditor.remove());
        let backlog = trigger.closest('.backlog');
        let backlogContent = backlog.querySelector('[data-role="content"]');
        let editor = quickCreateElement('div', {
            classList: ['backlog__editor'],
            parent: backlog,
            innerHTML: `
                <textarea data-role="input" data-get-mentionables data-positioning='{"bottom": "100%", "left": "0px", "right": "0px"}' data-reference='.backlog__editor'>${backlogContent.innerText}</textarea>
                <div data-role="cancel" data-command="remove-closest" data-target=".backlog__editor">Cancel</div>
                <div data-role="save">Save</div>
            `,
            eventListeners: {
                'keydown': (event) => {
                    let triggerSubmit = (event.key === 'Enter' && !event.shiftKey);
                    if (!triggerSubmit) {
                        return
                    };
                    event.preventDefault();
                    save();
                }
            }
        });
        let saveButton = document.querySelector('[data-role="save"]');
        saveButton.addEventListener('click', save);
    },
    'close_overlay': ({trigger, event, command}) => {
        trigger.closest('.layer')?.remove();
    },
    'get_emote_menu': async ({trigger, event, command}) => {
        let tooltip = await getView({
            name: 'emote-menu',
            kwargs: `{"group_chat_pk": ${groupChatPK}}`,
            format: 'html',
        });
        emoteMenuUtils.configureEmoteMenu({
            tooltip: tooltip, 
            handler: trigger.dataset.handler,
            kwargs: JSON.parse(trigger.dataset.kwargs),
        });
        tooltipManager.toggleTooltip({
            trigger: trigger,
            tooltip: tooltip,
            reference: trigger
        });
    },
    'react_backlog': ({trigger, event, command}) => {
        let backlog = trigger.closest('.backlog');

        chatSocket.send(JSON.stringify({
            'action': 'react_backlog',
            'emoticon_pk': trigger.dataset.emoticonPk,
            'kind': trigger.dataset.emoticonKind,
            'backlog_pk': backlog.dataset.pk
        }));
    },
    'toggle_select': ({trigger, event, command}) => {
        let select = trigger.closest('[data-role="select"]');
        let options = select.querySelector('[data-role="option-list"]');
        selectManager.toggleSelect({root: trigger, select: select, options: options});
    },
    'accept_invite': ({trigger, event, command}) => {
        chatSocket.send(JSON.stringify({
            'action': 'accept_invite',
            'directory': trigger.dataset.directory,
        }));
    },
    'leave_group_chat': ({trigger, event, command}) => {
        let prompt = trigger.closest('[data-role="prompt"]');
        if (!prompt.querySelector('input[name="confirm"]:checked')) {
            return;
        };
        chatSocket.send(JSON.stringify({
            'action': 'leave_group_chat',
        }));
    },
    'add_friend_from_profile': async ({trigger, event, command}) => {
        let response = await submitForm(trigger);
        if (response.status == 200) {
            trigger.classList.replace('profile__functional-button--generic', 'profile__functional-button--disabled')
            trigger.textContent = 'Friend Request Pending';
        };
    },
};