// JSON elements
let groupChatPK = document.getElementById('group-chat-pk');
groupChatPK = groupChatPK && JSON.parse(groupChatPK.innerText);

let groupChannelPK = document.getElementById('group-channel-pk');
let privateChatPK = document.getElementById('private-chat-pk');
let extraPath = document.getElementById('extra-path');

// Misc
const debug = true;

let websocketURL = 'ws://' + window.location.host + '/ws/app/'

if (groupChatPK) {
    websocketURL += `group-chat/${groupChatPK}/`;
    websocketURL += groupChannelPK ? `${JSON.parse(groupChannelPK.innerText)}/` : '';
}
else if (privateChatPK) {
    websocketURL += `private-chat/${JSON.parse(privateChatPK.innerText)}/`;
};

if (extraPath) {
    websocketURL += JSON.parse(extraPath.innerText) + '/';
};

chatSocket = new WebSocket(websocketURL);

window.onbeforeunload = function() {
    chatSocket.onclose = function () {};
    chatSocket.close();
};

chatSocket.onmessage = function(event) {
	let data = JSON.parse(event.data);
	let action = data.action;

    if (debug) {
        console.log(action)
        console.log(data)
        console.log('--------------------------------------')
    }

	let handler = chatSocketReceiveHandlers[action];
	handler(data);
};

chatSocket.onclose = function(event) {
    if (debug) {
        console.log('onclose');
    }
};

chatSocket.onopen = function() {
    if (debug) {
        console.log('opened')
    }

    if ((groupChannelPK || privateChatPK) && !document.hidden) {
        chatSocket.send(JSON.stringify({
            'action': 'mark_as_read',
        }));
    }
};

class FormSubmitListener {
    constructor() {
        this.init();
    };

    init() {
        document.addEventListener('submit', (event) => this.processSubmit(event));
    };

    async processSubmit(event) {
        this.form = event.target.closest('form');
        if (!this.form) {
            return;
        };

        event.preventDefault();
        let response = await submitForm(this.form);
        processForm({form: this.form, response: response});
        let onResponse = this.form.dataset.onResponse;
        let onResponseHandler = this[onResponse];
        if (onResponseHandler) {
            onResponseHandler(response);
        };
    };

    addEmote = ({status, html}) => {
        if (!(status === 200)) {
            return;
        };

        increaseCounter(document.getElementById('emote-manager'));
        this.form.closest('.layer').remove();
        let emoteManager = document.getElementById('emote-manager');
        let newItem = parseHTML(html);
        emoteManager.appendChild(newItem);
    };

    editEmote = ({status, id, name}) => {
        if (!(status === 200)) {
            return;
        };

        this.form.closest('.layer').remove();
        let emote = document.getElementById(id);
        emote.querySelector('[data-role="name"]').innerText = ':' + name + ':';
    };

    deleteEmote = ({id}) => {
        decreaseCounter(document.getElementById('emote-manager'));
        let emote = document.getElementById(id);
        emote.remove();
    };


}

window.addEventListener('submit', function delegateSubmit(event) {
    let form = event.target.closest('form');
    let command = form.dataset.submitCommand;
    if (Object.keys(submitHandlers).includes(command)) {
        event.preventDefault();
        submitHandlers[command](event);
    };
});

window.addEventListener('change', (event) => {
    let imageInput = event.target.closest('.image-input');
    if (!imageInput) {
        return;
    };

    let avatar = imageInput.querySelector('[data-role="image"]');
    let fileName = imageInput.querySelector('[data-role="filename"]');
    avatar.src=URL.createObjectURL(event.target.files[0]);
    fileName.innerText = event.target.files[0].name;
});

window.addEventListener('click', function preventRedirect(event) {
    if (event.target.closest('[data-prevent-redirect]')) {
        event.preventDefault();
    };
});

window.addEventListener('mouseup', function delegateClick(event) {
    if (!(event.button == 0)) {
        return;
    };
    for ([selector, handler] of Object.entries(windowClickHandlers)) {
        if (event.target.closest(selector)) {
			handler(event);
            return
		};
    };
});

// Close dropdowns
window.addEventListener('mouseup', (event) => {
	const eventDropdownContent = event.target.closest('.dropdown__content');
    const trigger = event.target.closest('.dropdown__trigger');
    const close = event.target.closest('.dropdown__close');
    let eventType;

    if (!trigger && !eventDropdownContent) {
        eventType = 'window click';
    }
    else if (eventDropdownContent) {
        eventType = 'dropdown click';
    };

    //
    if (eventType == 'window click' || close) {
        closeDropdowns();
    };

    if (eventType == 'dropdown click') {
        closeDropdowns(eventDropdownContent);
    }

    function closeDropdowns(skipElement) {
        let openDropdownContent = document.querySelectorAll('.dropdown__content--open');
        openDropdownContent.forEach((dropdownContent) => {
            if (dropdownContent == skipElement) {
                return;
            }
            
            if (dropdownContent.classList.contains('dropdown__content--static')) {
                return;
            }
            else {
                dropdownContent.classList.remove('dropdown__content--open');
            };
        });
    };
});


class TooltipManager {
    constructor() {
        this.init();
    };

    init() {
        this.tooltipLayer = document.querySelector('.layer--tooltips');

        document.addEventListener('mouseup', (event) => {
            let ignorableElements = event.target.closest('[data-active-tooltip-trigger], [data-command="get-tooltip"], .tooltip');
            if (ignorableElements) {
                return;
            };

            this.deregisterActiveTooltip();
        });
    };

    registerTooltip = ({trigger, tooltip, reference}) => {
        this.activeTrigger = trigger;
        this.activeTooltip = tooltip;
        this.activeTrigger.setAttribute('data-active-tooltip-trigger', '');

        let positioning = JSON.parse(trigger.dataset.positioning);
        this.tooltipLayer.appendChild(tooltip);

        positionFixedContainer(tooltip, reference, positioning);
        fitFixedContainer(tooltip);
    }

    deregisterActiveTooltip = () => {
        this.activeTooltip?.remove();
        this.activeTrigger?.removeAttribute('data-active-tooltip-trigger');

        this.activeTooltip = undefined;
        this.activeTrigger = undefined;
    }

    toggleTooltip = ({trigger, tooltip, reference}) => {
        if (!this.activeTooltip) {
            this.registerTooltip({trigger: trigger, reference: reference, tooltip: tooltip});
            return true;
        };

        if (trigger == this.activeTrigger) {
            this.deregisterActiveTooltip();
            return false;
        };

        this.deregisterActiveTooltip();
        this.registerTooltip({trigger: trigger, reference: reference, tooltip: tooltip});
        return true;    
    };

    
};

class EmoteMenuUtils {
    /* TODO: put the handlers for the menu here */
    configureEmoteMenu = ({tooltip, handler, kwargs}) => {
        tooltip.addEventListener('click', (event) => {
            this[handler]({event: event, ...kwargs});   
        });
    };

    reactBacklog = ({event, pk}) => {
        let emoticon = event.target.closest('.emote-menu__emote');
        if (!emoticon) {
            return;
        };

        chatSocket.send(JSON.stringify({
            'action': 'react_backlog',
            'backlog_pk': pk,
            'kind': emoticon.dataset.kind,
            'emoticon_pk': emoticon.dataset.pk,
        }));
    };
};

class MentionableObserver {
    constructor() {
        this.init();
    };

    init() {
        document.addEventListener('keydown', (event) => {
            this.activeElement = document.activeElement;

            if (this.activeElement.hasAttribute('data-get-mentionables')) {
                if ((event.code === 'Delete' || event.code === 'Backspace')) {
                    this.deleteHandler();
                }
                else if ((event.code === 'Enter')) {
                    this.enterHandler(event);
                };
            };

            if (this.openMentionablesList) {
                if (event.code === 'ArrowUp' || event.key === 'ArrowUp') {
                    event.preventDefault();
                    this.arrowUpHandler();
                } 
                else if (event.code === 'ArrowDown' || event.key === 'ArrowDown') {
                    event.preventDefault();
                    this.arrowDownHandler();
                }
            };
        });

        document.addEventListener('focusin', (event) => {
            // certain browsers won't fire selectionchange on focus
            this.activeElement = document.activeElement;

            if (!this.activeElement.hasAttribute('data-get-mentionables')) {
                return;
            };

            this.selectionHandler();
        })
    
        document.addEventListener('selectionchange', () => {
            this.activeElement = document.activeElement;

            if (!this.activeElement.hasAttribute('data-get-mentionables')) {
                return;
            };

            this.selectionHandler();
        });
    };

    closeMentionablesList = () => {
        tooltipManager.deregisterActiveTooltip();
        this.openMentionablesList = undefined;
        this.activeMentionable = undefined;
    };



    arrowUpHandler = () => {
        if (!this.activeMentionable) {
            this.activeMentionable = this.lastMentionable;
            this.activeMentionable?.classList.add(`mentionables-list__mentionable--active`);
            return;
        };

        let currentIndex = parseInt(this.activeMentionable.dataset.index);
        let newActiveMentionable = this.mentionablesNodes[currentIndex - 1];
        this.activeMentionable.classList.remove(`mentionables-list__mentionable--active`);
        this.activeMentionable = newActiveMentionable ? newActiveMentionable : this.lastMentionable;
        this.activeMentionable.classList.add(`mentionables-list__mentionable--active`);
    };

    arrowDownHandler = () => {
        if (!this.activeMentionable) {
            this.activeMentionable = this.firstMentionable;
            this.activeMentionable?.classList.add(`mentionables-list__mentionable--active`);
            return;
        };

        let currentIndex = parseInt(this.activeMentionable.dataset.index);
        let newActiveMentionable = this.mentionablesNodes[currentIndex + 1];
        this.activeMentionable.classList.remove(`mentionables-list__mentionable--active`);
        this.activeMentionable = newActiveMentionable ? newActiveMentionable : this.firstMentionable;
        this.activeMentionable.classList.add(`mentionables-list__mentionable--active`);
    };

    deleteHandler = () => {
        this.closeMentionablesList();
        this.selectionStart = this.activeElement.selectionStart - 1;

        let mention = getMention({
            i: this.selectionStart,
            input: this.activeElement.value
        });
    
        if (validateMention(mention)) {
            this.getMentionables(mention);
        };
    };

    enterHandler(event) {
        if (!this.activeMentionable) {
            this.closeMentionablesList();
            return;
        };
        
        event.preventDefault();
        let input = this.activeElement.value;
        let mentionStart = input.slice(0, this.selectionStart).lastIndexOf('>>');
        this.activeElement.value = (
            input.slice(0, mentionStart) 
            + '>>'
            + this.activeMentionable.dataset.value 
            + input.slice(this.selectionStart, -1)
            + ' '
        ); 
        this.closeMentionablesList();
    };

    selectionHandler = () => {
        this.closeMentionablesList();
        this.selectionStart = this.activeElement.selectionStart;

        let mention = getMention({
            i: this.selectionStart,
            input: this.activeElement.value
        });

        if (validateMention(mention)) {
            this.getMentionables(mention);
        };
    };

    buildMentionablesList = (html) => {
        this.openMentionablesList = parseHTML(html);
        tooltipManager.toggleTooltip({
            trigger: this.activeElement,
            tooltip: this.openMentionablesList,
            reference: this.tooltipReference
        });
        console.log(this.openMentionablesList)

        // to enable arrow navigation. Easier to handle enumerating them on frontend.
        this.mentionablesNodes = this.openMentionablesList.querySelectorAll('.mentionables-list__mentionable');
        this.mentionablesNodes?.forEach((mentionable, i) => mentionable.setAttribute('data-index', i));

        this.activeMentionable = this.openMentionablesList.querySelector('.mentionables-list__mentionable--active');        
        this.firstMentionable = this.mentionablesNodes[0];
        this.lastMentionable = this.mentionablesNodes[this.mentionablesNodes.length - 1];
    
        this.openMentionablesList.addEventListener('mouseover', (event) => this.mouseOverHandler(event));
        this.openMentionablesList.addEventListener('mousedown', (event) => this.mouseDownHandler(event));
    };

    mouseOverHandler = (event) =>  {
        let mentionable = event.target.closest('.mentionables-list__mentionable');
        if (!mentionable) {
            this.activeMentionable?.classList.remove('mentionables-list__mentionable--active');
            this.activeMentionable = undefined;
            return;
        };

        this.activeMentionable?.classList.remove('mentionables-list__mentionable--active');
        mentionable.classList.add('mentionables-list__mentionable--active');
        this.activeMentionable = mentionable;
    };

    mouseDownHandler  = (event) => {
        let mentionable = event.target.closest('.mentionables-list__mentionable');
        if (!mentionable) {
            return;
        };

        event.preventDefault();
        let input = this.activeElement.value;
        let mentionStart = input.slice(0, this.selectionStart).lastIndexOf('>>');
        this.activeElement.value = (
            input.slice(0, mentionStart) 
            + '>>'
            + this.activeMentionable.dataset.value 
            + input.slice(this.selectionStart, -1)
            + ' '
        ); 
        this.closeMentionablesList();
    };

    getMentionables = (mention) => {
        let referenceSelector = this.activeElement.dataset.reference;
        let reference = this.activeElement.closest(referenceSelector);
        this.tooltipReference = reference;
        
        chatSocket.send(JSON.stringify({
            'action': 'get_mentionables',
            'mention': mention,
        }));
    };
};

const mentionableObserver = new MentionableObserver();
const formSubmitListener = new FormSubmitListener();
const tooltipManager = new TooltipManager();
const emoteMenuUtils = new EmoteMenuUtils();