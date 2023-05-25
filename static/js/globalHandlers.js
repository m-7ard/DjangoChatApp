/*

    _commandHandlers

*/
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
	},
    'join-room': (event) => {
        let joinButton = event.target.closest('[data-command="join-room"]');
        chatSocketSendHandlers['join-room']({
            roomPk: joinButton.dataset.pk
        });
    }
};
/*

    _windowClickHandlers

*/
const windowClickHandlers = {
	'.dropdown__trigger': function toggleDropdown(event) {
		let dropdown = event.target.closest('.dropdown');
		let dropdownContent = dropdown.querySelector('.dropdown__content');
		dropdownContent.classList.toggle('dropdown__content--hidden');
	},
	'[data-command]': function delegateCommand(event) {
		let command = event.target.closest('[data-command]').dataset.command;
		console.log(command)
		commandHandlers[command](event);
	},
	'.tooltip__trigger': function delegateTooltipTrigger(event) {
        /* 
            This should be changed to use the id directly to eliminate
            the ambiguity
        */
		let trigger = event.target.closest('.tooltip__trigger');
		let tooltip = document.querySelector(trigger.dataset.target);
        tooltipHandlers[tooltip.id]({
            tooltip: tooltip,
            trigger: trigger,
        });
	},
	'.overlay__trigger': async function addOverlay(event) {
		event.preventDefault();
		
		let trigger = event.target.closest('.overlay__trigger');
		let viewName = trigger.dataset.viewName;
		
		let overlay = await overlayHandlers[viewName]({trigger, viewName});
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
/*

    _overlayHandlers

*/
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
		let overlay = document.createElement('div');
		overlay.innerHTML = response;
		return overlay
	},
	'update-channel': async ({trigger, viewName}) => {
		let pk = trigger.closest('[data-pk]').dataset.pk;
		let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
		url.searchParams.append('parameters', JSON.stringify({
			'channel': pk,
		}));
		let request = await fetch(url);
		let response = await request.text();
		let overlay = document.createElement('div');
		overlay.innerHTML = response;
		return overlay
	},
	'update-room': async ({trigger, viewName}) => {
		let pk = roomPk;
		let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
		url.searchParams.append('parameters', JSON.stringify({
			'room': pk,
		}));
		let request = await fetch(url);
		let response = await request.text();
		let overlay = document.createElement('div');
		overlay.innerHTML = response;
		let imageInput = overlay.querySelector('input[name="image"]');
		let imagePreview = imageInput.closest('.upload').querySelector('.upload__image img');
		imageInput.onchange = function(event) {
			let file = imageInput.value;
			imagePreview.src = file;
		}
		return overlay
	},
}
/*

    _tooltipHandlers

*/
const tooltipHandlers = {
	'friendship-menu': ({tooltip, trigger}) => {
		let friendshipPk = trigger.closest('.friendship').dataset.pk;
		tooltip.setAttribute('data-pk', friendshipPk);
	},
	'reactions': ({tooltip, trigger}) => {
		let kind = trigger.dataset.kind;
		if (kind == 'message-reaction') {
			let message = trigger.closest('.message');
			tooltip.onclick = (event) => commandHandlers['react-message-from-reactions']({event, message});
		}
		else if (kind == 'react-chatbar') {
			tooltip.onclick = (event) => commandHandlers['react-chatbar'](event);
		}
        else {
            throw Error('The data-kind attribute received from .tooltip__trigger is invalid. Check that it matches one of the kinds in tooltipHandlers["reactions"].')
        }
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
/*

    _chatSocketSendHandlers

*/
const chatSocketSendHandlers = {
	'ping': function(event) {
        console.log('pinged')
        chatSocket.send(JSON.stringify({
            'action': 'ping'
        }))
    },
	'requestServerResponse': async () => {
        try {
            // send the ping message to the server
            await chatSocket.send(JSON.stringify({
            'action': 'requestServerResponse'
            }));
            console.log('requestServerResponse');
        } catch (error) {
            console.error('Error requestServerResponse', error);
        }
    },
    'join-room': ({roomPk}) => {
        chatSocket.send(JSON.stringify({
            'action': 'join-room',
            'roomPk': roomPk
        }))
    }
};
/*

    _chatSocketReceiveHandlers

*/
const chatSocketReceiveHandlers = {
	'ping': chatSocketSendHandlers["ping"],
	'requestServerResponse': function() {
        console.log('response received')
    },
	'offline': function(data) {
        let user_references = document.querySelectorAll('.deez')
    },
	'create-room': function(data) {
        if (window.location.href.includes('room/' + data.pk)) {
            window.location = "{% url 'dashboard' %}"
        };
        let referenceNode = document.querySelector('.app-section--sidebar__modelbox--create-room');
        let newRoom = document.createElement('a');
        newRoom.setAttribute('href', `{% url 'room' ${data.pk} %}`);
        newRoom.setAttribute('class', "app-section--sidebar__modelbox app-section--sidebar__modelbox--joined-room");
        newRoom.innerHTML = (
            `
            <div class="app-section--sidebar__avatar app-section--sidebar__avatar--medium has-shadow">
                <img src="${data.image}" alt="">
            </div>
            <div class="wrapper--remaining-space">
                <div class="app-section--sidebar__infobox">
                    <div class="app-section--sidebar__name app-section--sidebar__name--medium">
                        ${data.name}
                    </div>
                </div>
            </div>
            `
        );
        referenceNode.parentNode.insertBefore(newRoom, referenceNode);
        document.querySelector('#room-count').innerText = parseInt(document.querySelector('#room-count').innerText) + 1;
    },	
	'remove-room': function(data) {
        if (window.location.href.includes('room/' + data.pk)) {
            window.location = "{% url 'dashboard' %}"
        };
        let roomReferences = [
            document.querySelector(`.app-section--sidebar__infobox[pk="${data.pk}"]`),
            // further room references...
        ];
        roomReferences.forEach((element) => element.remove())
    },
    'join-room': (data) {
        
    }
};