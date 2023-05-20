// JSON elements
const channelPk = JSON.parse(document.getElementById('channel-pk').textContent) || null;
const roomPk = JSON.parse(document.getElementById('room-pk').textContent) || null;
const userPk = JSON.parse(document.getElementById('user-id').textContent) || null;

// DOM elements
const dropdownContentContainers = document.querySelectorAll('.dropdown__content');
const tooltipContainers = document.querySelectorAll('.tooltip');

chatSocket = new WebSocket(
	'ws://'
	+ window.location.host
	+ '/ws/chat/'
	+ roomPk
	+ '/'
	+ channelPk
	+ '/'
);

chatSocket.onmessage = function(event) {
	let data = JSON.parse(event.data);
	let action = data.action;
	console.log(action)
	console.log(data)
	console.log('--------------------------------------')
	let handler = chatSocketReceiveHandlers[action];
	handler(data);
};

chatSocket.onclose = function(event) {
	console.log('onclose');
};

chatSocket.onopen = function() {
	/*
	NOTE: server hangs for some reason on some connections, 
		reason not clear
	NOTE-2: seems to be related to the way offline tracking was
		handled in the consumer, specific reason unclears
	*/
	console.log('opened')
	chatSocket.send(JSON.stringify({
		'action': 'requestServerResponse'
	}))
}

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
	}
};


const windowClickHandlers = {
	'.dropdown__trigger': function toggleDropdown(event) {
		let dropdown = event.target.closest('.dropdown');
		let dropdownContent = dropdown.querySelector('.dropdown__content');

		if (dropdownContent.classList.contains('dropdown__content--mouseleave')) {
			let selector = dropdownContent.dataset.mouseleaveTrigger;
			let boundary = event.target.closest(selector);
			boundary.addEventListener('mouseleave', boundaryMouseleave);
			function boundaryMouseleave() {
				dropdownContent.classList.toggle('dropdown__content--hidden');
				boundary.removeEventListener('mouseleave', boundaryMouseleave);
			};
		};

		dropdownContent.classList.toggle('dropdown__content--hidden');
	},
	'[data-command]': function delegateCommand(event) {
		let command = event.target.closest('[data-command]').dataset.command;
		console.log(command)
		commandHandlers[command](event);
	},

	'.tooltip__trigger': function delegateTooltipTrigger(event) {
		let trigger = event.target.closest('.tooltip__trigger');
		let tooltip = document.querySelector(trigger.dataset.target);
		Object.entries(tooltipHandlers).forEach(([selector, fn]) => {
			if (tooltip.classList.contains(selector) || tooltip.id == selector) {
				fn({
					tooltip: tooltip,
					trigger: trigger,
				});
			};
		})
	},
	'.overlay__trigger': async function addOverlay(event) {
		event.preventDefault();
		
		let trigger = event.target.closest('.overlay__trigger');
		let viewName = trigger.dataset.viewName;
		
		let html = await overlayHandlers[viewName]({trigger, viewName});
		let overlay = document.createElement('div');
		overlay.innerHTML = html;
		overlay.classList.add('layer');
		overlay.classList.add('layer--overlay');
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



};

const overlayHandlers = {
	'create-channel': async ({trigger, viewName}) => {
		let category = trigger.closest('.category');
		let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
		url.searchParams.append('parameters', JSON.stringify({
			'room': roomPk,
		}));
		url.searchParams.append('getData', JSON.stringify({
			'category': category.dataset.pk,
		}));
		let request = await fetch(url);
		let response = await request.text();
		return response
	},
	'update-channel': async ({trigger, viewName}) => {
		let pk = trigger.closest('[data-pk]').dataset.pk;
		let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
		url.searchParams.append('parameters', JSON.stringify({
			'channel': pk,
		}));
		let request = await fetch(url);
		let response = await request.text();
		return response
	}
}

const tooltipHandlers = {
	'friendship__menu': ({tooltip, trigger}) => {
		let friendshipPk = trigger.closest('.friendship').dataset.pk;
		tooltip.setAttribute('data-pk', friendshipPk);
	},
	'reactions': ({tooltip, trigger}) => {
		let kind = trigger.dataset.kind;
		if (kind == 'message_reaction') {
			let message = trigger.closest('.message');
			tooltip.onclick = (event) => {
				let reaction = event.target.closest('.reactions__reaction');
				if (!reaction) {
					return
				};
				
				chatSocketSendHandlers['react_message'](reaction.dataset.pk, message.dataset.pk);
			};
		}
		else if (kind == 'chatbar_reaction') {
			tooltip.onclick = (event) => {
				let chatbarInput = document.querySelector('.chatbar__input');
				let reaction = event.target.closest('.reactions__reaction');
				chatbarInput.value += `:${reaction.dataset.name}:`;
			};
		};
	},
	'profile': async ({tooltip, trigger}) => {
		let url = new URL(window.location.origin + '/GetHtmlElementFromModel/');
		let getRequestData = {
			'appLabel': 'rooms',
			'modelName': 'Member',
			'pk': trigger.dataset.pk,
			'contextVariable': 'member',
			'templateRoute': 'templates/rooms/elements/member-profile.html'
		};
		Object.entries(getRequestData).forEach(([key, value]) => url.searchParams.append(key, value));
		let request = await fetch(url);
		let response = await request.text();
		tooltip.innerHTML  = response;
		console.log(response);
	},
	'update-channel': ({tooltip, trigger}) => {
		let channel = trigger.closest('.channel');
		tooltip.setAttribute('data-pk', channel.dataset.pk);
	}
}

window.addEventListener('click', function delegateClick(event) {
	Object.entries(windowClickHandlers).forEach(([selector, handler]) => {
		if (event.target.closest(selector)) {
			handler(event);
		};
	});
});

/* Slides need a fixed maxHeight */
document.querySelectorAll('.dropdown__content--slide').forEach((content) => {
	content.style.maxHeight = content.offsetHeight + "px";
});

/*

1) Check if the event target is a dropdown trigger and save it to eventTrigger
2) Iterate over all dropdown__content elements that are:
	-not "static" (meant to stay open / only be closed by their own 
	dropdown__trigger being clicked).
	-not "semistatic" (meant to only close / be hidden through clicking off the content,
	or clicking a trigger).
3) If the dropdown__content's trigger is the same as the event target trigger (if there is
	one at all) it will not be hidden, and the default behaviour of triggerDropdown will
	trigger instead.

This will ensure that non-static dropdown__content will be hidden when a click occurs outside
of them on the window.

*/

window.addEventListener('click', function closeOpenDropdowns(event) {
	// Note: this does not handle dropdown open logic, only closing / hiding, for open logic see windowClickHandlers['.dropdown__trigger']
	let eventTrigger = event.target.closest('.dropdown__trigger');
	dropdownContentContainers.forEach((content) => {
		let contentTrigger = content.closest('.dropdown').querySelector('.dropdown__trigger');
		if (content.classList.contains('dropdown__content--static') || eventTrigger == contentTrigger) {
			return;
		};
		if (content.classList.contains('dropdown__content--semistatic') && 
			content.closest('.dropdown') == event.target.closest('.dropdown')) {
				return;
		};
		
		content.classList.add('dropdown__content--hidden');
	});
});

// Opening and Closing of tooltips is handled entirely by this (v) handler

window.addEventListener('click', function toggleTooltips(event) {
	const closeTooltips = (exception) => {
		tooltipContainers.forEach((tooltip) => {
			!(exception == tooltip) && tooltip.classList.add('tooltip--hidden');
		});
	};
	let eventTrigger = event.target.closest('.tooltip__trigger');
	let eventTooltip = event.target.closest('.tooltip');
	
	if (!eventTooltip && !eventTrigger) {
		closeTooltips();
	}

	if (eventTooltip) {
		let eventTooltipClose = event.target.closest('.tooltip__close');
		eventTooltipClose ? closeTooltips() : closeTooltips(eventTooltip);
	}

	if (eventTrigger) {
		let triggerTarget = document.querySelector(eventTrigger.dataset.target);
		closeTooltips(triggerTarget);
		if (triggerTarget.classList.contains('tooltip--hidden')) {
			let positioning = JSON.parse(eventTrigger.dataset.positioning);
			positionFixedContainer(triggerTarget, eventTrigger, positioning);
		};
		triggerTarget.classList.toggle('tooltip--hidden');
		fitFixedContainer(triggerTarget);
	};
});