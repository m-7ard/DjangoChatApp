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


function positionFixedContainer(element, reference, positioning) {
	// positioning arg needs to be a dict / object. Use JSON.parse on the data-positioning.
	let referenceDimensions = reference.getBoundingClientRect();
	
	//
	Object.entries(positioning).forEach(([key, value]) => {
		if (value.includes('%') && ['left', 'right'].includes(key)) { 
			positioning[key] = reference.offsetWidth * (parseInt(value.slice(0, -1)) / 100) + "px";
		}
		else if (value.includes('%') && ['top', 'bottom'].includes(key)) { 
			positioning[key] = reference.offsetHeight * (parseInt(value.slice(0, -1)) / 100) + "px";
		};
	});
	
	//
	if (positioning.top != undefined) {
		element.style.top = `calc(${referenceDimensions.top}px + calc(${positioning.top}))`;
	} else {
		element.style.top = '';
	};
	if (positioning.left != undefined) {
		element.style.left = `calc(${referenceDimensions.left}px + calc(${positioning.left}))`
	} else {
		element.style.left = '';
	};
	if (positioning.right != undefined) {
		element.style.right = `calc(${document.body.clientWidth - referenceDimensions.right}px - calc(${positioning.right}))`;
	} else {
		element.style.right = '';
	};
	if (positioning.bottom != undefined) {
		element.style.bottom = `calc(${document.body.clientHeight - referenceDimensions.bottom}px - calc(${positioning.bottom}))`;
	} else {
		element.style.bottom = '';
	};
};

function fitFixedContainer(element) {
	let elementDimensions = element.getBoundingClientRect();
	if (elementDimensions.bottom > document.body.clientHeight) {
		element.style.bottom = '0px';
		element.style.top = '';
	}; 
	if (elementDimensions.top < 0) {
		element.style.top = '0px';
		element.style.bottom = '';
	}; 
	if (elementDimensions.right > document.body.clientWidth) {
		element.style.right = '0px';
		element.style.left = '';
	}; 
	if (elementDimensions.left < 0) {
		element.style.left = '0px';
		element.style.right = '';
	};
};

function editClassList(element, {add, remove}) {
    add && add.forEach((classString) => element.classList.add(classString));
    remove && remove.forEach((classString) => element.classList.remove(classString));
};

function editAttributes(element, {attributes}) {
    attributes && Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
};

function quickCreateElement(elementTag, {classList, attributes, parent, eventListeners, innerHTML}) {
    /* elementTag: String, classList: Object, attributes: Object
        parent: HtmlNode, eventListeners: Object, innerHTML: String */
    const element = document.createElement(elementTag);
    if (classList) {
        editClassList(element, {add: classList});
    };
    if (attributes) {
        editAttributes(element, {attributes});
    };
    if (parent) {
        parent.appendChild(element);
    };
    if (eventListeners) {
        Object.entries(eventListeners).forEach(([kind, fn]) => element.addEventListener(kind, fn));
    };
    if (innerHTML) {
        element.innerHTML = innerHTML;
    };
    return element;
};

function processReaction({object, emote}) {
    let objectType = object.dataset.objectType;
    let objectPk = object.dataset.pk;
    let emotePk = emote.dataset.emotePk;
    chatSocketSendHandlers['react']({
        objectType: objectType,
        objectPk: objectPk,
        emotePk, emotePk
    });
}