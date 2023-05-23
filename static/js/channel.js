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
		'delete-message': function deleteMessageDB(event) {
			let message = event.target.closest('.message');
			chatSocket.send(JSON.stringify({
				'action': 'delete-message',
				'pk': message.dataset.pk
			}));
		},
		'react-message': function addOrRemoveReactionDB(reactionPk, messagePk) {
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
			editInput.remove()
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
		'delete-message': function deleteMessageDOM(data) {
			let pk = data.pk;
			let message = document.querySelector(`.message[data-pk="${pk}"]`);
			message.remove();
		},
		'react-message': function addOrRemoveReactionDB(data) {
			let {actionType, reactionPk, messagePk} = data;
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
		'delete-message': chatSocketSendHandlers['delete-message'],
		'edit-message': function editMessage(event) {
			// Close any open editors
            let messagesWithOpenEditors = document.querySelectorAll('.message--editing');
			messagesWithOpenEditors?.forEach((message) => {
				message.classList.remove('message--editing');
                message.querySelector('.message__edit').remove();
			});

            // Message DOM elements
			let message = event.target.closest('.message');
            let messageBody = message.querySelector('.message__body');
			let contentContainer = message.querySelector('.message__content');
			let editInput = quickCreateElement('textarea', {
                classList: ['message__edit'],
                attributes: {},
            });

            // Prompts for saving and canceling
            let prompts = quickCreateElement('div', {
                classList: ['message__prompts'],
                attributes: {},
            });
            prompts.innerHTML = `
                <span data-action="cancel">Cancel</span>
                <span data-action="save">Save</span>
            `;

            // Show message as being edited
			message.classList.add('message--editing');
			contentContainer.appendChild(editInput);
            messageBody.appendChild(prompts);

            // Put message content into the editor (emotes are converted to text)
            editInput.value = (Array.from(contentContainer.childNodes).reduce((accumulator, current) => {
                if (current.alt) {
                    accumulator += ':' + current.alt + ':';
                } 
                else if (current.textContent) {
                    accumulator += current.textContent;
                }
                else if (current.nodeName == 'BR') {
                    accumulator += '\n'
                }
                return accumulator;
            }, '')).trim(); // remove extra whitespace


            prompts.querySelector('[data-action="save"]').addEventListener('click', save);
            prompts.querySelector('[data-action="cancel"]').addEventListener('click', stopEditing);
			editInput.addEventListener('keypress', (e) => {
                if (!(e.key == "Enter") || (e.key === "Enter" && e.shiftKey)) {
                    return;
                };
                save();
            });
            
            function stopEditing () {
                message.classList.remove('message--editing');
                editInput.remove();
                prompts.remove();
            };

            function save () {
                message.classList.remove('message--editing');
                editInput.remove();
                prompts.remove();
                chatSocketSendHandlers['edit-message']({
                    'content': editInput.value,
                    'messagePk': message.dataset.pk, 
                });
            };
		},
		'react-message': function reactMessage(event) {
			let reaction = event.target.closest('.message__reaction');
			let reactionPk = reaction.dataset.pk;
			let message = event.target.closest('.message');
			let messagePk = message.dataset.pk;
			chatSocketSendHandlers['react-message'](reactionPk, messagePk);
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