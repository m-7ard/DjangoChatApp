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
		element.style.right = `calc(${document.body.clientWidth - referenceDimensions.right}px + calc(${positioning.right}))`;
	} else {
		element.style.right = '';
	};
	if (positioning.bottom != undefined) {
		element.style.bottom = `calc(${document.body.clientHeight - referenceDimensions.bottom}px + calc(${positioning.bottom}))`;
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

function parseHTML(string) {
    return new DOMParser().parseFromString(string, "text/html").querySelector('body > *');
};

function objectSelector(data) {
    return `[data-model="${data.model}"][data-app="${data.app}"][data-pk="${data.pk}"]`
}

function randomID() {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

async function getView({name, kwargs, query}) {
    let url = new URL(window.location.origin + '/GetViewByName/' + name);
    if (kwargs) {
        url.searchParams.append('kwargs', kwargs);
    };
    if (query) {
        url.searchParams.append('query', query);
    };
    let request = await fetch(url);
    let response = await request.text();
    return response;
}

async function processForm(event) {
    event.preventDefault();
    let form = event.target.closest('form');
    let request = await fetch(form.action, {
        method: form.method,
        body: new FormData(form)
    });
    let response = await request.json();
    // Remove old errors
    form.querySelectorAll('.field__message')?.forEach((error) => error.remove());


}

async function getTemplate({templateName, context}) {
    let url = new URL(window.location.origin + '/GetTemplate/');
    url.searchParams.append('template-name', templateName);
    if (context) {
        url.searchParams.append('context', context);
    };
    let request = await fetch(url);
    let response = await request.text();
    let template = parseHTML(response);
    return template;
}

function increaseCounter(element) {
    let counter = element.querySelector('[data-role="counter"]');
    let newCount = parseInt(counter.innerText) + 1;
    counter.innerText = newCount;
    return newCount;
}

function decreaseCounter(element) {
    let counter = element.querySelector('[data-role="counter"]');
    let newCount = parseInt(counter.innerText) - 1;
    counter.innerText = newCount;
    return newCount;
}

function addNotification(element) {
    let notification = element.querySelector('.app__notification');
    if (notification) {
        increaseCounter(notification);
    }
    else {
        notification = quickCreateElement('div', {
            classList: ['app__notification'],
            parent: element,
            innerHTML: '<div data-role="counter">1</div>'
        });
    };
}

function removeNotification(element) {
    let notification = element.querySelector('.app__notification');
    let newCount = decreaseCounter(notification);
    if (newCount == 0) {
        notification.remove();
    };
}