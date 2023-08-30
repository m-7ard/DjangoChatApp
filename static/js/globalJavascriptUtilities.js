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

function quickCreateElement(elementTag, {classList, attributes, parent, eventListeners, innerHTML, id}) {
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
    if (id) {
        element.id = id;
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
    const typedArray = new Uint8Array(10);
    const randomValues = window.crypto.getRandomValues(typedArray);
    return randomValues.join('');
}

async function getView({name, kwargs, query, format}) {
    let url = new URL(window.location.origin + '/GetViewByName/' + name);
    if (kwargs) {
        url.searchParams.append('kwargs', kwargs);
    };
    if (query) {
        url.searchParams.append('query', query);
    };
    let request = await fetch(url);
    let response;
    if (format == 'html') {
        response = await request.text();
        response = parseHTML(response);
    }
    else if (format == 'json') {
        response = await request.json();
    }
    else {
        response = await request.text();
    };
    return response;
}

async function processForm(event) {
    event.preventDefault();
    let form = event.target.closest('form');
    let formContainer = event.target.closest('.form');
    let formResponses = formContainer.querySelector('[data-role="form-responses"]');
    let request = await fetch(form.action, {
        method: form.method,
        body: new FormData(form)
    });
    let response = await request.json();
    // Remove old messages
    formContainer.querySelectorAll('.form__message').forEach((message) => message.remove());

    if (response.redirect) {
        window.location.replace(response.redirect);
    };

    if (response.status == 200) {
        // Success
        quickCreateElement('div', {
            classList: ['form__message', 'form__message--confirmation'],
            innerHTML: response.confirmation,
            parent: formResponses
        });
    }
    else if (response.status == 400) {
        // Error

        Object.entries(response.errors).forEach(([fieldName, errorList]) => {
            let field = formContainer.querySelector(`[data-name="${fieldName}"]`);
            let parent = field ? field : formResponses;

            errorList.forEach((error) => {
                let {code, message} = error;
                quickCreateElement('div', {
                    classList: ['form__message', 'form__message--error'],
                    innerHTML: message,
                    parent: parent
                });
            });
        });
    };
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
    counter.dataset.count = newCount;
    return newCount;
}

function decreaseCounter(element, times) {
    decreaseBy = times ? times : 1;
    let counter = element.querySelector('[data-role="counter"]');
    let newCount = parseInt(counter.innerText) - decreaseBy;
    counter.innerText = newCount;
    counter.dataset.count = newCount;
    return newCount;
}

function setCounter(element, newCount) {
    let counter = element.querySelector('[data-role="counter"]');
    counter.innerText = newCount;
    counter.dataset.count = newCount;
}

function addNotification(element, modifier) {
    let notification = element.querySelector('.notification');
    if (notification) {
        increaseCounter(notification);
    }
    else {
        let classList = ['notification'];
        modifier && classList.push(`notification--${modifier}`);
        notification = quickCreateElement('div', {
            classList: classList,
            parent: element,
            innerHTML: '<div data-role="counter">1</div>'
        });
    };
}

function removeNotification(element, times, modifier) {
    let selector = modifier ? `.notification--${modifier}` : '.notification';
    let notification = element.querySelector(selector);
    let newCount = decreaseCounter(notification, times);
    if (newCount == 0) {
        notification.remove();
    };
};

function scrollbarAtBottom(element) {
    return element.scrollHeight - Math.round(element.scrollTop) - element.clientHeight <= 1;
};

function getMention(input) {
    /*
    Captures all mentions in format >>[optional a-z/0-9]#[optional 0-9, max chars 2]
    */
    const pattern = /^>>[a-zA-Z0-9]*#?\d{0,2}$/g;
    const matches = input.match(pattern) || [];
    return matches[matches.length - 1]
};