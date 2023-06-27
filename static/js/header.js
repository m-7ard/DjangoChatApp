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


window.addEventListener('mouseup', function delegateClick(event) {
	Object.entries(windowClickHandlers).forEach(([selector, handler]) => {
		if (event.target.closest(selector)) {
			handler(event);
		};
	});
});


// Close dropdowns
window.addEventListener('mouseup', (event) => {
	const eventDropdownContent = event.target.closest('.dropdown__content');
    const trigger = event.target.closest('.dropdown__trigger');
    const close = event.target.closest('.dropdown__close');
    let eventType;
    if (!trigger && !eventDropdownContent) {
        eventType = 'window click';
    }
    else if (eventDropdownContent) {
        eventType = 'dropdown click';
    };

    //
    if (eventType == 'window click' || close) {
        closeDropdowns();
    };

    if (eventType == 'dropdown click') {
        closeDropdowns(eventDropdownContent);
    }

    function closeDropdowns(skipElement) {
        let openDropdownContent = document.querySelectorAll('.dropdown__content--open');
        openDropdownContent.forEach((dropdownContent) => {
            if (dropdownContent == skipElement) {
                return;
            }
            
            if (dropdownContent.classList.contains('dropdown__content--static')) {
                return;
            }
            else {
                dropdownContent.classList.remove('dropdown__content--open');
            };
        });
    };
});


// Close tooltips
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