const tooltipHandlers = {
	'emotes': ({tooltip, trigger}) => {
		let kind = trigger.dataset.kind;

		if (kind == 'backlog') {
			let object = trigger.closest(`[data-object-type]`);
			tooltip.onclick = (event) => {
				let emote = event.target.closest('.emotes__emote');
				if (!emote || !object) { 
					return
				};
				commandHandlers['react']({
					objectPk: object.dataset.objectPk,
					objectType: object.dataset.objectType,
					emotePk: emote.dataset.emotePk
				});
				
			};
		}
		else if (kind == 'chatbar') {
			let chatbarInput = document.querySelector('.chatbar__input');
			tooltip.onclick = (event) => {
				let emote = event.target.closest('.emotes__emote');
				if (!emote) {
					return;
				};
				commandHandlers['emote-to-text']({
					target: chatbarInput,
					emote: emote
				});
			};
		}
		else {
			throw Error('The data-kind attribute received from .tooltip__trigger is invalid. Check that it matches one of the kinds in tooltipHandlers["emotes"].')
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
	'friend-menu': ({tooltip, trigger}) => {
		tooltip.onclick = (event) => {
			let command = trigger.dataset.localCommand;
			if (!command) {
				return
			};

			let friendship = trigger.closest('[data-object-type="friendship"]');
			let friend  = trigger.closest('[data-object-type="friend"]');

			if (command == 'manage-friendship') {
				commandHandlers['manage-friendship']({
					friendshipPk: friendship.dataset.objectPk,
					friendPk: friend.dataset.objectPk,
					kind: trigger.dataset.kind
				});
			}
			else if (command == 'react') {
				
			}
		}
	},
	
}