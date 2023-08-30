
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