window.addEventListener('load', () => {
	/*

	-------------------------
	chatSocket SEND Handlers
	-------------------------
	
	*/
	Object.assign(chatSocketSendHandlers, {
		'send-message': function submitMessage(event) {
			if (!(event.key == "Enter") || (event.key === "Enter" && event.shiftKey)) {
				return;
			};
			event.preventDefault();
			chatSocket.send(JSON.stringify({
				'action': 'send-message',
				'content': chatbarInput.value.trim()
			}));
			chatbarInput.value = '';
		},
		'delete-message': function deleteMessageDB({messagePk}) {
			chatSocket.send(JSON.stringify({
				'action': 'delete-message',
				'messagePk': messagePk
			}));
		},
		'react-message': ({reactionPk, messagePk}) => {
			chatSocket.send(JSON.stringify({
				'action': 'react-message',
				'reactionPk': reactionPk,
				'messagePk': messagePk
			}));
		},
		'edit-message': function editMessageDB({messagePk, content}) {
			chatSocket.send(JSON.stringify({
				'action': 'edit-message',
				'messagePk': messagePk,
				'content': content
			}));
		},
	});

	/*

	-------------------------
	chatSocket RECEIVE Handlers
	-------------------------

	*/

	Object.assign(chatSocketReceiveHandlers, {
		'send-message': function receiveMessage(data) {
			let message = new DOMParser().parseFromString(data.html, "text/html").querySelector('.message');
			appMessages.appendChild(message);
			appMessages.scrollTo(0, appMessages.scrollHeight);
		},
		'delete-message': function deleteMessageDOM({messagePk}) {
			let message = document.querySelector(`.message[data-pk="${messagePk}"]`);
			message.remove();
		},
		'react-message': function addOrRemoveReactionDB({actionType, reactionPk, messagePk}) {
			console.log(actionType, reactionPk, messagePk)
			let message = document.querySelector(`.message[data-pk="${messagePk}"]`);
			let messageReactions = message.querySelector('.message__reactions');
			if (actionType == ['addReaction']) {
				let reaction = messageReactions.querySelector(`.message__reaction[data-pk="${reactionPk}"]`);
				reaction.classList.add('message__reaction--selected');
				let counter = reaction.querySelector('.message__counter');
				counter.innerText = parseInt(counter.innerText) + 1;
			}
			else if (actionType == ['removeReaction']) {
				let reaction = messageReactions.querySelector(`.message__reaction[data-pk="${reactionPk}"]`);
				reaction.classList.remove('message__reaction--selected');
				let counter = reaction.querySelector('.message__counter');
				counter.innerText = parseInt(counter.innerText) - 1;
			}
			else if (actionType == ['createReaction']) {
				let reaction = document.createElement('span');
				reaction.classList.add('message__reaction');
				reaction.classList.add('message__reaction--selected');
				reaction.classList.add('has-shadow');
				reaction.dataset.pk = reactionPk;
				reaction.dataset.command = "react";
				reaction.innerHTML = `
				<img src="${data.url}" alt="">
				<span class="message__counter">1</span>
				`;
				messageReactions.appendChild(reaction);
			}
			else if (actionType == ['deleteReaction']) {
				let reaction = messageReactions.querySelector(`.message__reaction[data-pk="${reactionPk}"]`);
				reaction.remove();
			}
		},
		'edit-message': function editMessageDOM(data) {
			let {messagePk, content} = data;
			let message = document.querySelector(`.message[data-pk="${messagePk}"]`);
			let contentContainer = message.querySelector('.message__content');
			contentContainer.innerHTML = content;
		},
		'response': () => { console.log('response exists') }
	});

	/*

	-------------------------
	window COMMAND Handlers
	-------------------------

	*/


	Object.assign(commandHandlers, {
		'delete-message': (event) => {
            let message = event.target.closest('.message');
            chatSocketSendHandlers['delete-message']({
                'messagePk': message.dataset.pk,
            })
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
			editInput.addEventListener('keypress', (e) => {
                if (!(e.key == "Enter") || (e.key === "Enter" && e.shiftKey)) {
                    return;
                };
                save();
            });
            
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
		'react-message-from-message': (event) => {
			let reaction = event.target.closest('.message__reaction');
			let reactionPk = reaction.dataset.pk;
			let message = event.target.closest('.message');
			let messagePk = message.dataset.pk;
			chatSocketSendHandlers['react-message']({
                messagePk,
                reactionPk, 
            });
		},
		'react-message-from-reactions': ({event, message}) => {
            /* 
                This function is called from tooltipHandlers['reactions'] 
            */
            let reaction = event.target.closest('.reactions__reaction');
            if (!reaction) {
                return
            };
            
            chatSocketSendHandlers['react-message']({
                'reactionPk': reaction.dataset.pk,
                'messagePk': message.dataset.pk,
            });
        },
        'react-chatbar': (event) => {
            let chatbarInput = document.querySelector('.chatbar__input');
            let reaction = event.target.closest('.reactions__reaction');
            chatbarInput.value += `:${reaction.dataset.name}:`;
        },
		'open_profile': function openProfile(event) {
			
		},
	});

	// DOM Elements
	const chatbarInput = document.querySelector('.chatbar__input');
	const appMessages = document.querySelector('#app__messages');
	
	// Scroll to bottom
	appMessages.scrollTo(0, appMessages.scrollHeight);

	// Chatbar enter listener
	chatbarInput.addEventListener('keypress', chatSocketSendHandlers['send-message'])
});