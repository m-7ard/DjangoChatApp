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
        /**************
            TODO: SAVE IMAGE ON BACKEND TO ACTUALLY DISPLAY IT */
		let imageInput = overlay.querySelector('input[name="image"]');
		let imagePreview = imageInput.closest('.upload').querySelector('.upload__image img');
		imageInput.onchange = function(event) {
			let file = imageInput.value;
			imagePreview.src = file;
		}
        /**************/
		return overlay
	},
    'leave-room': async ({trigger, viewName}) => {
        let pk = roomPk;
        let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
        url.searchParams.append('parameters', JSON.stringify({
			'room': pk,
		}));
		let request = await fetch(url);
		let response = await request.text();
        let overlay = quickCreateElement('div', {
            innerHTML: response,
        });
        return overlay
    },
}