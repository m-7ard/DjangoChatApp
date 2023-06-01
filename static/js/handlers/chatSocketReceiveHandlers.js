const chatSocketReceiveHandlers = {
	'requestServerResponse': function() {
        console.log('response received')
    },
	'offline': function(data) {
        let user_references = document.querySelectorAll('.deez')
    },
	'create-room': function(data) {
        if (window.location.href.includes('room/' + data.pk)) {
            window.location = "{% url 'dashboard' %}"
        };
        let referenceNode = document.querySelector('.app-section--sidebar__modelbox--create-room');
        let newRoom = document.createElement('a');
        newRoom.setAttribute('href', `{% url 'room' ${data.pk} %}`);
        newRoom.setAttribute('class', "app-section--sidebar__modelbox app-section--sidebar__modelbox--joined-room");
        newRoom.innerHTML = (
            `
            <div class="app-section--sidebar__avatar app-section--sidebar__avatar--medium has-shadow">
                <img src="${data.image}" alt="">
            </div>
            <div class="wrapper--remaining-space">
                <div class="app-section--sidebar__infobox">
                    <div class="app-section--sidebar__name app-section--sidebar__name--medium">
                        ${data.name}
                    </div>
                </div>
            </div>
            `
        );
        referenceNode.parentNode.insertBefore(newRoom, referenceNode);
        document.querySelector('#room-count').innerText = parseInt(document.querySelector('#room-count').innerText) + 1;
    },	
	'remove-room': function(data) {
        if (window.location.href.includes('room/' + data.pk)) {
            window.location = "{% url 'dashboard' %}"
        };
        let roomReferences = [
            document.querySelector(`.app-section--sidebar__infobox[pk="${data.pk}"]`),
            // further room references...
        ];
        roomReferences.forEach((element) => element.remove())
    },
    'join-room': ({html}) => {
        let appMessages = document.querySelector('#app__messages');
        let log = new DOMParser().parseFromString(html, "text/html").querySelector('.log');
		appMessages.appendChild(log);
		appMessages.scrollTo(0, appMessages.scrollHeight);
    },
    'leave-room': ({html}) => {
        let appMessages = document.querySelector('#app__messages');
        let log = new DOMParser().parseFromString(html, "text/html").querySelector('.log');
		appMessages.appendChild(log);
		appMessages.scrollTo(0, appMessages.scrollHeight);
    },
    'manage-friendship': (friendshipPk, friendPk, kind, category, html) => {
        console.log(kind)
        /*
            TODO: for some reason this is undefined, find and fix
        */
        if (kind == 'create') {
            let userGroup = document.querySelector(`.user-group__content[data-category="${category}"]`);
            let friend = parseHTML(html);
            userGroup.appendChild(friend);
        }
        else if (kind == 'accept') {
            let userGroup = document.querySelector(`.user-group__content[data-category="${category}"]`);
            let friend = document.querySelector(`.friend[data-object-pk=${friendshipPk}]`);
            userGroup.appendChild(friend);
        }
        else if (kind == 'reject' || kind == 'remove') {
            let friend = document.querySelector(`.friend[data-object-pk="${friendPk}"]`);
            console.log(friend)
            friend.remove();
        }
    },
    'send-message': function receiveMessage(data) {
        let message = new DOMParser().parseFromString(data.html, "text/html").querySelector('body > *');
        let appMessages = document.querySelector('#app-messages');
        appMessages.appendChild(message);
        appMessages.scrollTo(0, appMessages.scrollHeight);
    },
    'delete-backlog': ({objectType, objectPk}) => {
        let objectSelector = '.backlog';
        objectSelector += `[data-object-type="${objectType}"]`;
        objectSelector += `[data-pk="${objectPk}"]`;
        let object = document.querySelector(objectSelector);
        object.remove();
    },
    'react': ({actionType, emotePk, objectType, objectPk, imageUrl}) => {
        let objectSelector;
        let objectReactionSelector;
        if (objectType == 'message') {
            objectSelector = '.backlog';
            objectReactionSelector = '.backlog__reactions';
        }
        else if (objectType == 'log') {
            objectSelector = '.backlog';
            objectReactionSelector = '.backlog__reactions';
        }

        objectSelector += `[data-object-type="${objectType}"]`
        objectSelector += `[data-pk="${objectPk}"]`
        
        let object = document.querySelector(objectSelector);
        let objectReactions = object.querySelector(objectReactionSelector);
        
        if (actionType == ['addReaction']) {
            let reaction = objectReactions.querySelector(`[data-emote-pk="${emotePk}"]`);
            reaction.classList.add('reaction--selected');
            let counter = reaction.querySelector('.reaction__counter');
            counter.innerText = parseInt(counter.innerText) + 1;
        }
        else if (actionType == ['removeReaction']) {
            let reaction = objectReactions.querySelector(`[data-emote-pk="${emotePk}"]`);
            reaction.classList.remove('reaction--selected');
            let counter = reaction.querySelector('.reaction__counter');
            counter.innerText = parseInt(counter.innerText) - 1;
        }
        else if (actionType == ['createReaction']) {
            quickCreateElement('span', {
                parent: objectReactions,
                classList: ['reaction', 'reaction--selected'],
                attributes: {'data-emote-pk': emotePk, 'data-command': 'react'},
                innerHTML: `
                    <img src="${imageUrl}" alt="">
                    <span class="reaction_counter">1</span>
                `,
            });
        }
        else if (actionType == ['deleteReaction']) {
            let reaction = objectReactions.querySelector(`[data-emote-pk="${emotePk}"]`);
            reaction.remove();
        }
    },
    'edit-message': function editMessageDOM(data) {
        let {messagePk, content} = data;
        let message = document.querySelector(`.message[data-pk="${messagePk}"]`);
        let contentContainer = message.querySelector('.message__content');
        contentContainer.innerHTML = content;
    },
    'response': () => { console.log('response exists') },

};