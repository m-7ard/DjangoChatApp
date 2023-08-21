// JSON elements
const groupChatPK = document.getElementById('group-chat-pk');
const groupChannelPK = document.getElementById('group-channel-pk');
const privateChatPK = document.getElementById('private-chat-pk');
const extraPath = document.getElementById('extra-path');

// DOM elements
const dropdownContentContainers = document.querySelectorAll('.dropdown__content');
const tooltipContainers = document.querySelectorAll('.tooltip');

// Misc
const debug = true;

let websocketURL = 'ws://' + window.location.host + '/ws/app/'

if (groupChatPK) {
    websocketURL += `group-chat/${JSON.parse(groupChatPK.innerText)}/`;
    websocketURL += groupChannelPK ? `${JSON.parse(groupChannelPK.innerText)}/` : '';
}
else if (privateChatPK) {
    websocketURL += `private-chat/${JSON.parse(privateChatPK.innerText)}/`;
};

if (extraPath) {
    websocketURL += JSON.parse(extraPath.innerText) + '/';
};

chatSocket = new WebSocket(websocketURL);

window.onbeforeunload = function() {
    chatSocket.onclose = function () {};
    chatSocket.close();
};

chatSocket.onmessage = function(event) {
	let data = JSON.parse(event.data);
	let action = data.action;

    if (debug) {
        console.log(action)
        console.log(data)
        console.log('--------------------------------------')
    }

	let handler = chatSocketReceiveHandlers[action];
	handler(data);
};

chatSocket.onclose = function(event) {
    if (debug) {
        console.log('onclose');
    }
};

chatSocket.onopen = function() {
    if (debug) {
        console.log('opened')
    }

    if ((groupChannelPK || privateChatPK) && !document.hidden) {
        chatSocket.send(JSON.stringify({
            'action': 'mark_as_read',
        }));
    }
};

window.addEventListener('submit', function delegateSubmit(event) {
    let form = event.target.closest('form');
    let command = form.dataset.submitCommand;
    if (Object.keys(submitHandlers).includes(command)) {
        event.preventDefault();
        submitHandlers[command](event);
    };
});

window.addEventListener('click', function preventRedirect(event) {
    if (event.target.closest('[data-prevent-redirect]')) {
        event.preventDefault();
    };
});

window.addEventListener('mouseup', function delegateClick(event) {
    if (!(event.button == 0)) {
        return;
    };
    for ([selector, handler] of Object.entries(windowClickHandlers)) {
        if (event.target.closest(selector)) {
			handler(event);
            return
		};
    };
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
    // only capture left clicks
    if (!(event.button == 0)) {
        return;
    };
    
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