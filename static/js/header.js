// JSON elements
const channelPk = JSON.parse(document.getElementById('channel-pk').textContent) || null;
const roomPk = JSON.parse(document.getElementById('room-pk').textContent) || null;
const userPk = JSON.parse(document.getElementById('user-id').textContent) || null;

// DOM elements
const dropdownContentContainers = document.querySelectorAll('.dropdown__content');
const tooltipContainers = document.querySelectorAll('.tooltip');

// Tooltip context
const tooltipContext = {};


let websocketUrl = 'ws://' + window.location.host;
if (roomPk) {
    websocketUrl += '/ws/chat/' + String(roomPk) + '/';

    if (channelPk) {
        websocketUrl += String(channelPk) + '/';
    };
}
else {
    websocketUrl += '/ws/app/';
}

chatSocket = new WebSocket(websocketUrl);

window.onbeforeunload = function() {
    chatSocket.onclose = function () {};
    chatSocket.close();
};

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

window.addEventListener('mouseup', (event) => {
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


window.addEventListener('mouseup', (event) => {
	let tooltip = event.target.closest('.tooltip');
	let trigger = event.target.closest('.tooltip__trigger');
    let close = event.target.closest('.tooltip__close');

    if (!trigger && !tooltip) {
        let openTooltip = document.querySelector('.tooltip');
        openTooltip?.remove();
    };

    if (close) {
        tooltip.remove();
    };
});