window.addEventListener('load', () => {
	/*

	-------------------------
	chatSocket SEND Handlers
	-------------------------
	
	*/
	Object.assign(chatSocketSendHandlers, {
		'send_message': function submitMessage(event) {
			if (!(event.key == "Enter") || (event.key === "Enter" && event.shiftKey)) {
				return;
			};
			event.preventDefault();
			chatSocket.send(JSON.stringify({
				'action': 'send_message',
				'content': chatbarInput.value.trim()
			}));
			chatbarInput.value = '';
		},
		'delete_message': function deleteMessageDB(event) {
			let message = event.target.closest('.message');
			chatSocket.send(JSON.stringify({
				'action': 'delete_message',
				'pk': message.dataset.pk
			}));
		},
		'react_message': function addOrRemoveReactionDB(reactionPk, messagePk) {
			chatSocket.send(JSON.stringify({
				'action': 'react_message',
				'reactionPk': reactionPk,
				'messagePk': messagePk
			}));
		},
		'edit_message': function editMessageDB(event) {
			if (!(event.key == "Enter") || (event.key === "Enter" && event.shiftKey)) {
				return;
			};
			event.preventDefault();
			let editInput = event.target;
			let message = event.target.closest('.message');
			let contentContainer = editInput.closest('.message__content');
			contentContainer.classList.remove('message__content--editing');
			chatSocket.send(JSON.stringify({
				'action': 'edit_message',
				'messagePk': message.dataset.pk,
				'content': editInput.value.trim()
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
		'send_message': function receiveMessage(data) {
			let message = new DOMParser().parseFromString(data.html, "text/html").querySelector('.message');
			appMessages.appendChild(message);
			appMessages.scrollTo(0, appMessages.scrollHeight);
		},
		'delete_message': function deleteMessageDOM(data) {
			let pk = data.pk;
			let message = document.querySelector(`.message[data-pk="${pk}"]`);
			message.remove();
		},
		'react_message': function addOrRemoveReactionDB(data) {
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
		'edit_message': function editMessageDOM(data) {
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
		'delete_message': chatSocketSendHandlers['delete_message'],
		'edit_message': function editMessage(event) {
			// close any open editors
			document.querySelectorAll('.message__content--editing')?.forEach((element) => {
				element.classList.remove('message__content--editing');
				element.querySelector('.message__edit').remove()
			});

			let message = event.target.closest('.message');
			let contentContainer = message.querySelector('.message__content');
			let contentContainerCopy = contentContainer.cloneNode(true);
			contentContainer.classList.add('message__content--editing');
			let editInput = document.createElement('textarea');
			editInput.classList.add('message__edit');
			contentContainerCopy.querySelectorAll('img').forEach((img) => {
				img.replaceWith(`:${img.alt}:`);
			});
			editInput.value = contentContainerCopy.textContent.trim();
			editInput.addEventListener('keypress', chatSocketSendHandlers['edit_message']);
			contentContainer.appendChild(editInput);
		},
		'react_message': function reactMessage(event) {
			let reaction = event.target.closest('.message__reaction');
			let reactionPk = reaction.dataset.pk;
			let message = event.target.closest('.message');
			let messagePk = message.dataset.pk;
			chatSocketSendHandlers['react_message'](reactionPk, messagePk);
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
	chatbarInput.addEventListener('keypress', chatSocketSendHandlers['send_message'])
});