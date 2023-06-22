
const windowClickHandlers = {
	'.dropdown__trigger': (event) => {
		let dropdown = event.target.closest('.dropdown');
		let dropdownContent = dropdown.querySelector('.dropdown__content');
		dropdownContent.classList.toggle('dropdown__content--hidden');
	},
	'[data-command]': (event) => {
        event.preventDefault();
		let trigger = event.target.closest('[data-command]');
        let command = trigger.dataset.command;
        let handler = commandHandlers[command];
        handler(event);
	},
	'.tooltip__trigger': async (event) => {
        event.preventDefault();
		let trigger = event.target.closest('.tooltip__trigger');
        let openTooltip = document.querySelector('.tooltip');
        if (openTooltip) {
            if (openTooltip.dataset.randomId == trigger.dataset.randomId) {
                openTooltip.remove();
                return;
            }
            else {
                openTooltip.remove();
            };
        };
        let target = trigger.dataset.target;
        let contextObject = trigger.closest('[data-context]');
        let tooltipLayer = document.querySelector('.layer--tooltips');
        let url = new URL(window.location.origin + '/tooltip/' + target);
        if (contextObject) {
            url.searchParams.append('context', contextObject.dataset.context);
        };
        let request = await fetch(url);
        let response = await request.text();
        let tooltip = parseHTML(response);
        let sharedID = randomID()
        tooltip.setAttribute('data-random-id', sharedID)
        trigger.setAttribute('data-random-id', sharedID)

        let positioning = JSON.parse(trigger.dataset.positioning);
        positionFixedContainer(tooltip, trigger, positioning);
        tooltipLayer.appendChild(tooltip);
        fitFixedContainer(tooltip);
	},
    '.overlay__trigger': async (event) => {
        event.preventDefault();
		let trigger = event.target.closest('.overlay__trigger');
        let target = trigger.dataset.target;
        let contextObject = trigger.closest('[data-context]');
        let url = new URL(window.location.origin + '/overlay/' + target);
        if (contextObject) {
            url.searchParams.append('context', contextObject.dataset.context);
        };
        let request = await fetch(url);
        let overlay = await request.text();
        let overlayLayer = quickCreateElement('div', {
            classList: ['layer', 'layer--overlay'],
            innerHTML: overlay,
            parent: document.body,
            eventListeners: {
                'mouseup': (e) => {
                    if (!(e.target.closest('.overlay')) || (e.target.closest('.overlay__close'))) {
                        overlayLayer.remove();
                    };
                },
            },
        });
        if (Object.keys(overlayHandlers).includes(target)) {
            overlayHandlers[target]({trigger, overlayLayer});
        };
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