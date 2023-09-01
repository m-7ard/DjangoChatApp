const chatSocketReceiveHandlers = {
	'requestServerResponse': function() {
        console.log('response received')
    },
	'offline': function(data) {
        let user_references = document.querySelectorAll('.deez')
    },
	'create-group-chat': function({html}) {
        let groupChat = parseHTML(html);
        let referenceElement = document.getElementById('insert-group-chat');
        referenceElement.parentNode.insertBefore(groupChat, referenceElement);
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
        let appMessages = document.querySelector('#app-messages');
        let log = parseHTML(html);
		appMessages.appendChild(log);
		appMessages.scrollTo(0, appMessages.scrollHeight);
    },
    'leave-room': ({html}) => {
        let appMessages = document.querySelector('#app-messages');
        let log = parseHTML(html);
		appMessages.appendChild(log);
		appMessages.scrollTo(0, appMessages.scrollHeight);
    },
    'manage-friendship': ({frienship, kind, category, html}) => {
        if (kind == 'create') {
            let userGroup = document.querySelector(`.user-group__content[data-category="${category}"]`);
            let friend = parseHTML(html);
            userGroup.appendChild(friend);
        }
        else if (kind == 'accept') {
            let userGroup = document.querySelector(`.user-group__content[data-category="${category}"]`);
            let friendship = document.querySelector(objectSelector(frienship));
            let friend = friendship.closest('[data-model="CustomUser"]');
            friend.innerHTML = parseHTML(html).innerHTML;
            userGroup.appendChild(friend);
        }
        else if (['reject', 'remove', 'cancel'].includes(kind)) {
            let friendship = document.querySelector(objectSelector(frienship));
            let friend = friendship.closest('[data-model="CustomUser"]');
            friend.remove();
        };
    },

    'delete-backlog': ({objectType, objectPk}) => {
        let objectSelector = '.backlog';
        objectSelector += `[data-object-type="${objectType}"]`;
        objectSelector += `[data-object-pk="${objectPk}"]`;
        let object = document.querySelector(objectSelector);
        object.remove();
    },
    'react': ({model, app, pk, emotePk, actionType, imageUrl}) => {
        let objectSelector;
        let objectReactionSelector;
        if (model == 'Message' || model == 'Log') {
            objectSelector = '.backlog';
            objectReactionSelector = '.backlog__reactions';
        }

        objectSelector += `[data-model="${model}"]`
        objectSelector += `[data-app="${app}"]`
        objectSelector += `[data-pk="${pk}"]`
        
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
    'edit-message': ({message, content}) => {
        let backlog = document.querySelector(objectSelector(message));
        let backlogContent = backlog.querySelector('.backlog__content');
        backlogContent.innerHTML = content;
    },
    
    'response': () => { console.log('response exists') },

    'create_message': ({html, pk, is_sender}) => {
        let newMessage = parseHTML(html);
        let scrollbarWasAtBottom = scrollbarAtBottom(backlogs);
        backlogs.appendChild(newMessage);
        
        if (!document.hidden && (scrollbarWasAtBottom || is_sender)) {
            backlogs.scrollTop = backlogs.scrollHeight;
        };

        if (!document.hidden && scrollbarAtBottom(backlogs)) {
            chatSocket.send(JSON.stringify({
                'action': 'mark_as_read',
            }));
            return;
        };

        if (!is_sender) {
            let unreadBacklogsSubheader = document.getElementById('unread-backlogs-subheader');
            increaseCounter(unreadBacklogsSubheader);
            let unreadBacklogsDivider = document.getElementById('unread-backlogs-divider');
            if (unreadBacklogsDivider) {
                // there are unread backlogs already
                return
            };
            let divider = quickCreateElement('div', {
                classList: ['app__divider', 'app__divider--unread-backlogs'],
                id: 'unread-backlogs-divider',
            });
            backlogs.insertBefore(divider, newMessage);
        }    
    },
    'scroll_to_bottom': ({id}) => {
        let element = document.getElementById(id);
        element.scrollTo(0, element.scrollHeight);
    },
    'create_friendship': ({html, is_receiver}) => {
        let section;
        if (is_receiver) {
            section = document.getElementById('incoming-pending-friendships');
        }
        else {
            section = document.getElementById('outgoing-pending-friendships');
        }
        section.appendChild(parseHTML(html));
        increaseCounter(section);
    },
    'accept_friendship': ({pk, is_receiver}) => {
        let friend = document.getElementById(`friend-${pk}`);
        friend.querySelector('.user__icons').remove();
        decreaseCounter(friend.closest('.sidebar__section'));
        
        let section = document.getElementById('accepted-friendships');
        section.appendChild(friend);
        increaseCounter(section);

        if (is_receiver) {
            let dashboardButton = document.getElementById('dashboard-button');
            removeNotification(dashboardButton);
        };
    },
    'delete_friendship': ({pk, was_receiver}) => {
        let friend = document.getElementById(`friend-${pk}`);
        decreaseCounter(friend.closest('.sidebar__section'));
        if (was_receiver) {
            let dashboardButton = document.getElementById('dashboard-button');
            removeNotification(dashboardButton);
        };
        friend.remove();
    },
    'create_notification': ({id, modifier}) => {
        let element = document.getElementById(id);
        addNotification(element, modifier);
    },
    'remove_notification': ({id, times, modifier}) => {
        let element = document.getElementById(id);
        console.log(element)
        removeNotification(element, times, modifier);
    },
    'create_private_chat': ({html}) => {
        let privateChats = document.getElementById('private-chats');
        privateChats.appendChild(parseHTML(html));
    },
    'remove_all_notifications': ({id, modifier}) => {
        let element = document.getElementById(id);
        let selector = modifier ? `.notification--${modifier}` : '.notification';
        element.querySelectorAll(selector).forEach((element) => element.remove());
    },
    'mark_as_read': ({}) => {
        let unreadBacklogsDivider = document.getElementById('unread-backlogs-divider');
        unreadBacklogsDivider?.remove();
        let unreadBacklogsSubheader = document.getElementById('unread-backlogs-subheader');
        setCounter(unreadBacklogsSubheader, 0);
    },
    'delete_backlog': ({pk}) => {
        let backlog = document.getElementById(`backlog-${pk}`);
        backlog.remove();
    },
    'edit_message': ({pk, content}) => {
        let backlog = document.getElementById(`backlog-${pk}`);
        if (!backlog) {
            return;
        };
        let backlogContent = backlog.querySelector('[data-role="content"]');
        backlogContent.innerText = content;
    },
    'generate_backlogs': ({html, page}) => {
        backlogs.scrollTo(0, 1);
        let backlogList = parseHTML(html);
        backlogs.prepend(...[...backlogList.childNodes].reverse());
        if (page === 1) {
            backlogs.scroll(0, backlogs.scrollHeight);
        };
    },
    'get_mentionables': ({html}) => mentionableObserver.buildMentionablesList(html),

};