function positionFixedContainer(element, reference, positioning) {
	// positioning arg needs to be a dict / object. Use JSON.parse on the data-positioning
    // before passing it in.
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
		element.style.top = 'auto';
	}; 
	if (elementDimensions.top < 0) {
		element.style.top = '0px';
		element.style.bottom = element.style.bottom ? element.style.bottom : 'auto';
	}; 
	if (elementDimensions.right > document.body.clientWidth) {
		element.style.right = '0px';
	}; 
	if (elementDimensions.left < 0) {
		element.style.left = '0px';
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

async function submitForm(form) {
    let request = await fetch(form.action, {
        method: form.method,
        body: new FormData(form),
    });
    let response = await request.json();
    return response;
};

function processForm({form, response}) {
    // Remove old messages
    form.querySelectorAll('.form__response').forEach((message) => message.remove());
    let formResponses = form.querySelector('[data-role="form-responses"]');

    if (response.redirect) {
        window.location.replace(response.redirect);
    };

    if (response.status == 200) {
        // Success

        if (!response.confirmation) {
            return;
        };

        quickCreateElement('div', {
            classList: ['form__response', 'form__response--success'],
            innerHTML: response.confirmation,
            parent: formResponses,
        });
    }
    else if (response.status == 400) {
        // Error

        if (!response.errors) {
            return;
        };
        
        Object.entries(response.errors).forEach(([fieldName, errorList]) => {
            let field = form.querySelector(`[data-name="${fieldName}"]`);
            let parent = field ? field : formResponses;
            
            errorList.forEach((error) => {
                let {code, message} = error;
                quickCreateElement('div', {
                    classList: ['form__response', 'form__response--error'],
                    innerHTML: message,
                    parent: parent
                });
            });
        });
    };
};

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
    let decreaseBy = times ? times : 1;
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

function addNotification(element, notification_id, kind) {
    let notification = element.querySelector(`.notification[data-notification-kind="${kind}"]`);
    let elementNotifications = JSON.parse(element.dataset.notifications);
    elementNotifications[notification_id] = elementNotifications[notification_id] ? elementNotifications[notification_id] + 1 : 1;
    element.setAttribute('data-notifications', JSON.stringify(elementNotifications));
    increaseCounter(notification);
}

function removeNotification(element, notification_id, kind) {
    let notification = element.querySelector(`.notification[data-notification-kind="${kind}"]`);
    let elementNotifications = JSON.parse(element.dataset.notifications);
    let decreaseBy =  elementNotifications[notification_id]
    if (!decreaseBy) {
        return;
    };
    decreaseCounter(notification, decreaseBy);
    elementNotifications[notification_id] = 0;
    element.setAttribute('data-notifications', JSON.stringify(elementNotifications));
};

function scrollbarAtBottom(element) {
    return element.scrollHeight - Math.round(element.scrollTop) - element.clientHeight <= 1;
};

function getMention({i, input}) {
    let precedingString = input.slice(0, i);
    let mentionStart = precedingString.lastIndexOf('>>');

    if (mentionStart === -1) {
        return;
    };
    
    if (!(mentionStart === 0) && !(input.charAt(mentionStart-1) === ' ' || input.charAt(mentionStart-1) === '\n')) {
        return;
    };
 
    return precedingString.slice(mentionStart, i+1);
};

function validateMention(mention) {
    if (!mention) {
        return;
    };

    /*
    validates format >>[optional a-z/0-9]#[optional 0-9, max chars 2]
    */
    const pattern = /^>>[a-zA-Z0-9]*#?\d{0,2}$/g;
    return pattern.test(mention);
};