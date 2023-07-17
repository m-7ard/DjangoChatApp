
const windowClickHandlers = {
	'[data-command]': (event) => {
		let trigger = event.target.closest('[data-command]');
        let command = trigger.dataset.command;
        let handler = commandHandlers[command];
        handler({trigger, event, command});
	},
    '.dropdown__trigger': (event) => {
		let dropdown = event.target.closest('.dropdown');
		let dropdownContent = dropdown.querySelector('.dropdown__content');
		dropdownContent.classList.toggle('dropdown__content--open');
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
        let tooltip = await getTemplate({
            templateName: trigger.dataset.templateName,
            context: trigger.dataset.context,
        });
        let sharedID = randomID()
        tooltip.setAttribute('data-random-id', sharedID)
        trigger.setAttribute('data-random-id', sharedID)
        let tooltipLayer = document.querySelector('.layer--tooltips');
        let positioning = JSON.parse(trigger.dataset.positioning);
        positionFixedContainer(tooltip, trigger, positioning);
        tooltipLayer.appendChild(tooltip);
        fitFixedContainer(tooltip);
	},
    '.overlay__trigger': async (event) => {
        event.preventDefault();
		let trigger = event.target.closest('.overlay__trigger');
        let contextObject = trigger.closest('[data-context]');
        let overlay = await getTemplate({
            templateName: trigger.dataset.templateName,
            context: contextObject.dataset.context,
        });
        let overlayLayer = quickCreateElement('div', {
            classList: ['layer', 'layer--overlay'],
            innerHTML: overlay.outerHTML,
            parent: document.body,
            eventListeners: {
                'mouseup': (e) => {
                    if (!(e.target.closest('.overlay'))) {
                        overlayLayer.remove();
                    };
                },
            },
        });
    },
};