
const windowClickHandlers = {
	'.dropdown__trigger': (event) => {
		let dropdown = event.target.closest('.dropdown');
		let dropdownContent = dropdown.querySelector('.dropdown__content');
		dropdownContent.classList.toggle('dropdown__content--hidden');
	},
	'[data-command]': (event) => {
		let trigger = event.target.closest('[data-command]');
        let command = trigger.dataset.command;
		console.log(command)
		let args = processCommandEvent[command](event);
        commandHandlers[command](args);
	},
	'.tooltip__trigger': (event) => {
		let trigger = event.target.closest('.tooltip__trigger');
		let tooltip = document.querySelector(trigger.dataset.target);

        tooltipHandlers[tooltip.id]({
            tooltip: tooltip,
            trigger: trigger,
        });
	},
	'.overlay__trigger': async (event) => {
		event.preventDefault();
		
		let trigger = event.target.closest('.overlay__trigger');
		let viewName = trigger.dataset.viewName;
		
		let overlay = await overlayHandlers[viewName]({trigger, viewName});
		editClassList(overlay, {add: ['layer', 'layer--overlay']});
		let closeButtons = overlay.querySelectorAll('.overlay__close');
		closeButtons.forEach((closeButton) => closeButton.addEventListener('click', () => overlay.remove()));
		document.body.appendChild(overlay);
	},
	'.select__trigger': function toggleSelect(event) {
		let trigger = event.target.closest('.select__trigger');
		let select = trigger.closest('.select');
		select.classList.toggle('select--active');
		window.addEventListener('click', (newEvent) => {
			let newSelect = newEvent.target.closest('.select');
			if (newSelect == select) {
				return
			}

			select?.classList.remove('select--active');
		}, {once: true});
	},
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
		'react-message': ({emotePk, messagePk}) => {
            /* Parameter check for the sake of making debugging easier */
            if (!emotePk || !messagePk) {
                let missing = [];
                if (!emotePk) { missing.push('emotePk') };
                if (!messagePk) { missing.push('messagePk') };
                throw Error(`chatSocketSendHandlers['react-message'] is missing ${missing}`);
            };
			chatSocket.send(JSON.stringify({
				'action': 'react-message',
				'emotePk': emotePk,
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
};