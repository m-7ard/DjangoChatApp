async function getModelData(app_label, model_name, pk, keys) {
	const url = new URL(window.location.origin + '/RequestData/');
	url.searchParams.append('model_name', model_name);
	url.searchParams.append('app_label', app_label);
	url.searchParams.append('pk', pk);
	url.searchParams.append('keys', JSON.stringify(keys));
	try {
		const response = await fetch(url);
		return await response.json();
	} 
	catch (error) {
		console.error(error);
		throw error;
	};
};

async function getForm(form_path, kwargs) {
	let url = new URL(form_path);
	kwargs && Object.entries(kwargs).forEach(([key, value]) => url.searchParams.append(key, value));
	const response = await fetch(url);
	const formHtml = await response.text();
	return formHtml;
}



/* getReverseUrl is not being used for now */

async function getReverseUrl(name, parameters) {
	let fetchUrl = new URL(
		window.location.origin 
		+ '/get_reverse_url/' 
		+ name
		+ '/'
	);

	fetchUrl.searchParams.append('parameters', JSON.stringify(parameters))
	const response = await fetch(fetchUrl);
	const viewUrl = await response.text();
	return viewUrl
}