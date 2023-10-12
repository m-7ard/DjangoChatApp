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

        let responseHandler = this[response.handler];
        if (responseHandler) {
            responseHandler(response);
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

    editEmote = ({status, pk, name}) => {
        if (!(status === 200)) {
            return;
        };

        this.form.closest('.layer').remove();
        let emote = document.getElementById(`emote-${pk}`);
        emote.querySelector('[data-role="name"]').innerText = ':' + name + ':';
    };

    deleteEmote = ({pk}) => {
        decreaseCounter(document.getElementById('emote-manager'));
        let emote = document.getElementById(`emote-${pk}`);
        emote.remove();
    };

    deleteInvite = ({pk}) => {
        let invite = document.getElementById(`invite-${pk}`);
        invite.remove();
    };
    
    createInvite = ({directory}) => {
        this.form.closest('.layer--overlay').remove();
        let inviteDisplay = document.getElementById('invite-display');
        inviteDisplay.value = directory;
    };

    updateInvite = ({html}) => {
        let invite = this.form.closest('.backlog-invite');
        invite.replaceWith(parseHTML(html));
    };

    createRole = ({html}) => {
        this.form.closest('.layer--overlay').remove();
        let manager = document.getElementById('role-manager');
        manager.appendChild(parseHTML(html));
    };

    editRole = ({pk, html}) => {
        this.form.closest('.layer--overlay').remove();
        let role = document.getElementById(`role-${pk}`);
        role.outerHTML = html;
    };

    deleteRole = ({pk}) => {
        let role = document.getElementById(`role-${pk}`);
        role.remove();
    };

    editRoleMemberCount = ({pk, count}) => {
        this.form.closest('.layer--overlay').remove();
        let role = document.getElementById(`role-${pk}`);
        let memberCount = role.querySelector('[data-role="member-count"]');
        memberCount.textContent = count;
    }
}

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

class TooltipUtils {
    adjustTooltip = (event) => {
        let {trigger, tooltip, reference} = this.getAttributes();
        let positioning = JSON.parse(trigger.dataset.positioning);
        positionFixedContainer(tooltip, reference, positioning);
        fitFixedContainer(tooltip);
    };

    checkAndCloseTooltip = (event) => {
        let closeTrigger = event.target.closest('[data-tooltip-close]');
        if (closeTrigger) {
            this.closeTooltip();
            return;
        };

        let ignorableElements = event.target.closest(this.ignorableElements.join(', '));
        if (ignorableElements) {
            return;
        };
        this.closeTooltip();
    };
};

class TooltipManager extends TooltipUtils {
    constructor() {
        super();
        this.tooltipLayer = document.querySelector('.layer--tooltips');
        this.closeTooltip = this.deregisterActiveTooltip;
        this.ignorableElements = ['[data-active-tooltip-trigger]', '[data-command="get-tooltip"]', '.tooltip'];
    };

    getAttributes = () => {
        return {trigger: this.activeTrigger, tooltip: this.activeTooltip, reference: this.reference};
    };

    registerTooltip = ({trigger, tooltip, reference}) => {
        this.activeTrigger = trigger;
        this.activeTooltip = tooltip;
        this.activeTrigger.setAttribute('data-active-tooltip-trigger', '');
        this.reference = reference;
        this.tooltipLayer.appendChild(tooltip);
        this.adjustTooltip();
        window.addEventListener('resize', this.adjustTooltip);
        window.addEventListener('mouseup', this.checkAndCloseTooltip);
    }

    deregisterActiveTooltip = () => {
        window.removeEventListener('resize', this.adjustTooltip);
        window.removeEventListener('mouseup', this.checkAndCloseTooltip);
        this.activeTooltip.remove();
        this.activeTrigger.removeAttribute('data-active-tooltip-trigger');
        this.activeTooltip = undefined;
        this.activeTrigger = undefined;
        this.reference = undefined;
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

class EmoteMenuManager extends TooltipUtils {
    constructor() {
        super();
        this.tooltipLayer = document.querySelector('.layer--tooltips');
        this.ignorableElements = ['.emote-menu', '[data-active-tooltip-trigger]'];
        this.closeTooltip = this.closeEmoteMenu;
    };

    closeEmoteMenu = () => {
        if (!this.activeEmoteMenu) {
            return;
        };

        this.activeEmoteMenu.remove();
        this.activeEmoteMenu = undefined;
        this.activeTrigger = undefined;

        window.removeEventListener('resize', this.adjustTooltip);
        window.removeEventListener('mouseup', this.checkAndCloseTooltip);
    };

    getAttributes = () => {
        return {trigger: this.activeTrigger, tooltip: this.activeEmoteMenu, reference: this.activeTrigger};
    };

    getEmoteMenu = ({trigger}) => {
        this.waitingTrigger = trigger;
        console.log(this.waitingTrigger)
        chatSocket.send(JSON.stringify({
            'action': 'get_emote_menu'
        }));
    };

    buildEmoteMenu = ({tooltip, emoji_categories}) => {
        this.activeTrigger = this.waitingTrigger;
        this.waitingTrigger = undefined;

        let handler = this[this.activeTrigger.dataset.handler];
        let kwargs = JSON.parse(this.activeTrigger.dataset.kwargs);

        
        this.activeEmoteMenu = quickCreateElement('div', {
            innerHTML: tooltip
        }).firstChild;
        this.activeEmoteMenu.addEventListener('click', (event) => handler({event: event, ...kwargs}));
        this.activeTrigger.setAttribute('data-active-tooltip-trigger', '');
        
        this.tooltipLayer.append(this.activeEmoteMenu);
        this.adjustTooltip();
        window.addEventListener('resize', this.adjustTooltip);
        window.addEventListener('mouseup', this.checkAndCloseTooltip);
        window.setTimeout(() => {
            let content = this.activeEmoteMenu.querySelector('[data-role="content"]');
            emoji_categories.forEach((category) => {
                let html = parseHTML(category);
                content.appendChild(html);
            });
        }, 50);
    };

    toggleEmoteMenu = ({trigger}) => {
        if (this.waitingTrigger) {
            return;
        };

        if (!this.activeEmoteMenu) {
            this.getEmoteMenu({trigger});
            return true;
        };

        if (trigger == this.activeTrigger) {
            this.closeEmoteMenu();
            return false;
        };

        this.closeEmoteMenu();
        this.getEmoteMenu({trigger});
        return true;
    }

    reactBacklog = ({event, pk}) => {
        let emoticon = event.target.closest('[data-role="emoticon"]');
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

    emoteToText = ({event, target}) => {
        let emoticon = event.target.closest('[data-role="emoticon"]');
        if (!emoticon) {
            return;
        };
        
        let input = document.getElementById(target);
        input.value += ':' + emoticon.dataset.name + ':';
    };
};

class MentionableObserver extends TooltipUtils {
    constructor() {
        super();
        this.tooltipLayer = document.querySelector('.layer--tooltips');
        this.ignorableElements = ['.mentionables-list', '[data-get-mentionables]'];
        this.closeTooltip = this.closeMentionablesList;
        this.init();
    };

    init() {
        document.addEventListener('keydown', (event) => {
            if (document.activeElement.hasAttribute('data-get-mentionables')) {
                this.activeElement = document.activeElement;
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
            if (!document.activeElement.hasAttribute('data-get-mentionables')) {
                return;
            };

            this.activeElement = document.activeElement;
            this.selectionHandler();
        })
    
        document.addEventListener('selectionchange', (event) => {
            if (!document.activeElement.hasAttribute('data-get-mentionables')) {
                return;
            };

            this.activeElement = document.activeElement;
            this.selectionHandler();
        });
    };

    closeMentionablesList = () => {
        if (!this.openMentionablesList) {
            return;
        };

        this.openMentionablesList.remove();
        this.openMentionablesList = undefined;
        this.activeMentionable = undefined;

        window.removeEventListener('resize', this.adjustTooltip);
        window.removeEventListener('mouseup', this.checkAndCloseTooltip);
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

    mouseDownHandler = (event) => {
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

        // to enable arrow navigation. Easier to handle enumerating them on frontend.
        this.mentionablesNodes = this.openMentionablesList.querySelectorAll('.mentionables-list__mentionable');
        this.mentionablesNodes?.forEach((mentionable, i) => mentionable.setAttribute('data-index', i));

        this.activeMentionable = this.openMentionablesList.querySelector('.mentionables-list__mentionable--active');        
        this.firstMentionable = this.mentionablesNodes[0];
        this.lastMentionable = this.mentionablesNodes[this.mentionablesNodes.length - 1];
    
        this.openMentionablesList.addEventListener('mouseover', (event) => this.mouseOverHandler(event));
        this.openMentionablesList.addEventListener('mousedown', (event) => this.mouseDownHandler(event));
        
        this.tooltipLayer.append(this.openMentionablesList);
        this.adjustTooltip();
        window.addEventListener('resize', this.adjustTooltip);
        window.addEventListener('mouseup', this.checkAndCloseTooltip);
    };

    getMentionables = (mention) => {
        let referenceSelector = this.activeElement.dataset.reference;
        this.tooltipReference = this.activeElement.closest(referenceSelector);
        
        chatSocket.send(JSON.stringify({
            'action': 'get_mentionables',
            'mention': mention,
        }));
    };

    getAttributes = () => {
        return {trigger: this.activeElement, tooltip: this.openMentionablesList, reference: this.tooltipReference};
    };
};

class SelectManager extends TooltipUtils {
    constructor() {
        super();
        this.ignorableElements = ['[data-command="toggle_select"]', '[data-role="option"]']
        this.closeTooltip = this.deregisterActiveSelect;
    };

    getAttributes = () => {
        return {trigger: this.activeRoot, tooltip: this.activeOptionList, reference: this.activeRoot};
    };

    toggleSelect = ({root, select, options}) => {
        if (!this.activeSelect) {
            this.registerSelect({root: root, select: select, options: options});
            return true;
        };

        if (root == this.activeRoot) {
            this.deregisterActiveSelect();
            return false;
        };

        this.deregisterActiveSelect();
        this.registerSelect({root: root, select: select, options: options});
        return true;
    }

    registerSelect = ({root, select, options}) => {
        this.activeSelect = select;
        this.activeSelect.addEventListener('click', this.selectOption);
        this.activeRoot = root;
        this.activeSelect.setAttribute('data-open', '');
        this.activeOptionList = options;
        this.adjustTooltip();
        window.addEventListener('resize', this.adjustTooltip);
        window.addEventListener('mouseup', this.checkAndCloseTooltip);
    };

    deregisterActiveSelect = () => {
        window.removeEventListener('resize', this.adjustTooltip);
        window.removeEventListener('mouseup', this.checkAndCloseTooltip);
        this.activeSelect.removeEventListener('click', this.selectOption);
        this.activeSelect.removeAttribute('data-open');
        this.activeSelect = undefined;
        this.activeRoot = undefined;
        this.activeOptionList = undefined;
    }

    selectOption = (event) => {
        let option = event.target.closest('[data-role="option"]');
        if (!option) {
            return;
        };

        this.activeRoot.innerText = option.innerText;
        this.deregisterActiveSelect();
    }
}

class FormSorterControls {
    updateInput(element) {
        let sorter = element.closest('[data-role="sorter"]');
        let input = sorter.querySelector('input');

        let sorterElements = Array.from(sorter.querySelectorAll('[data-role="sorter-element"]'));
        input.value = JSON.stringify([...sorterElements.map((element) => {
            return parseInt(element.dataset.value);
        })]);
    };

    raiseElement(currentElement) {
        let precedingElement = currentElement.previousElementSibling;
        if (!precedingElement || precedingElement.tagName.toLowerCase() == 'input') {
            return;
        };

        precedingElement.insertAdjacentElement('beforebegin', currentElement);
        this.updateInput(currentElement);
    };

    lowerElement(currentElement) {
        let nextElement = currentElement.nextElementSibling;
        if (!nextElement || nextElement.tagName.toLowerCase() == 'input') {
            return;
        };

        nextElement.insertAdjacentElement('afterend', currentElement);
        this.updateInput(currentElement);
    };
}

const mentionableObserver = new MentionableObserver();
const formSubmitListener = new FormSubmitListener();
const tooltipManager = new TooltipManager();
const emoteMenuManager = new EmoteMenuManager();
const selectManager = new SelectManager();
const formSorterControls = new FormSorterControls();