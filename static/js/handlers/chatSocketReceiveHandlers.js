const chatSocketReceiveHandlers = {
	'requestServerResponse': function() {
        console.log('response received')
    },
	'create-group-chat': function({html}) {
        let groupChat = parseHTML(html);
        let referenceElement = document.getElementById('insert-group-chat');
        referenceElement.parentNode.insertBefore(groupChat, referenceElement);
    },	

    'response': () => { console.log('response exists') },

    'create_message': ({html, is_sender, is_mentioned}) => {
        let newMessage = parseHTML(html);
        is_mentioned ? newMessage.classList.add('backlog--mentioned') : undefined;
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
    'edit_message': ({pk, content, is_mentioned}) => {
        let backlog = document.getElementById(`backlog-${pk}`);
        if (!backlog) {
            return;
        };
        console.log(is_mentioned)
        is_mentioned ? backlog.classList.add('backlog--mentioned') : backlog.classList.remove('backlog--mentioned');
        let backlogContent = backlog.querySelector('[data-role="content"]');
        backlogContent.innerHTML = content;
    },
    'generate_backlogs': ({html, page}) => {
        backlogs.scrollTo(0, 1);
        let backlogList = parseHTML(html);
        backlogs.prepend(...[...backlogList.childNodes].reverse());
        if (page === 1) {
            backlogs.scroll(0, backlogs.scrollHeight);
        };
    },
    'get_mentionables': ({html}) => {
        mentionableObserver.buildMentionablesList(html)
    },
    'create_reaction': ({html, backlog_pk, is_sender}) => {
        let backlog = document.getElementById(`backlog-${backlog_pk}`);
        let reactions = backlog.querySelector('[data-role="reactions"]');
        let reaction = parseHTML(html);
        is_sender && reaction.classList.add('backlog__reaction--selected');
        reactions.appendChild(reaction);
    },
    'delete_reaction': ({reaction_pk}) => {
        let reaction = document.getElementById(`reaction-${reaction_pk}`);
        reaction.remove();
    },
    'add_reaction': ({reaction_pk, is_sender}) => {
        let reaction = document.getElementById(`reaction-${reaction_pk}`);
        is_sender && reaction.classList.add('backlog__reaction--selected');
        increaseCounter(reaction);
    },
    'remove_reaction': ({reaction_pk, is_sender}) => {
        let reaction = document.getElementById(`reaction-${reaction_pk}`);
        is_sender && reaction.classList.remove('backlog__reaction--selected');
        decreaseCounter(reaction);
    },

};