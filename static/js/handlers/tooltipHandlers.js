const tooltipHandlers = {
	'friendship-menu': ({tooltip, trigger}) => {
		let friendshipPk = trigger.closest('.friendship').dataset.pk;
		tooltip.setAttribute('data-pk', friendshipPk);
	},
	'emotes': ({tooltip, trigger}) => {
		let kind = trigger.dataset.kind;

		if (['message', 'log'].includes(kind)) {
			let object = trigger.closest(`[data-object-type="${kind}"]`);
			tooltip.onclick = (event) => {
                let emote = event.target.closest('.emotes__emote');
                if (!emote || !object) { 
                    return
                };
                processReaction({
                    object: object,
                    emote: emote
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
	'update-channel': ({tooltip, trigger}) => {
		let channel = trigger.closest('.channel');
		tooltip.setAttribute('data-pk', channel.dataset.pk);
	}
}