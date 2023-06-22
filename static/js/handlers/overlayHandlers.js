/*

TODO: Get rid of overlay handlers althogether and use the same logic as 
tooltips (?)

goal is to get room-menu to work, have a bit of separation of interests

*/

const overlayHandlers = {
    'create-room': async ({trigger, viewName}) => {
        let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
		let request = await fetch(url);
		let response = await request.text();
		let layer = document.createElement('div');
		layer.innerHTML = response;
		return layer
	},
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
		let layer = document.createElement('div');
		layer.innerHTML = response;
		return layer
	},

	'update-channel': async ({trigger, viewName}) => {
		let pk = trigger.closest('[data-pk]').dataset.pk;
		let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
		url.searchParams.append('parameters', JSON.stringify({
			'channel': pk,
		}));
		let request = await fetch(url);
		let response = await request.text();
		let layer = document.createElement('div');
		layer.innerHTML = response;
		return layer
	},
	'update-room': async ({trigger, viewName}) => {
		let pk = roomPk;
		let url = new URL(window.location.origin + '/GetViewByName/' + viewName + '/');
		url.searchParams.append('parameters', JSON.stringify({
			'room': pk,
		}));
		let request = await fetch(url);
		let response = await request.text();
		let layer = document.createElement('div');
		layer.innerHTML = response;
        /**************
            TODO: SAVE IMAGE ON BACKEND TO ACTUALLY DISPLAY IT */
		let imageInput = layer.querySelector('input[name="image"]');
		let imagePreview = imageInput.closest('.upload').querySelector('.upload__image img');
		imageInput.onchange = function(event) {
			let file = imageInput.value;
			imagePreview.src = file;
		}
        /**************/
		return layer
	},
}