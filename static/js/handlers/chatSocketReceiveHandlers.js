const chatSocketReceiveHandlers = {
	'requestServerResponse': function() {
        console.log('response received')
    },
	'create_group_chat': function({html}) {
        let groupChat = parseHTML(html);
        let referenceElement = document.getElementById('insert-group-chat');
        referenceElement.parentNode.insertBefore(groupChat, referenceElement);
    },
    'create_group_channel': ({html, category}) => {
        let channel = parseHTML(html);
        if (category) {
            let categorySection = document.getElementById(`category-${category}`);
            categorySection.append(channel);
        }
        else {
            let groupChannels = document.getElementById('group-channels');
            groupChannels.appendChild(channel);
        };
    },
    'create_group_category': ({html}) => {
        let groupChannels = document.getElementById('group-channels');
        let lastCategory = groupChannels.querySelector('[data-role="category"]:last-of-type');
        let category = parseHTML(html);

        if (lastCategory) {
            lastCategory.insertAdjacentElement('afterend', category);
            return;
        }

        let firstChannel = groupChannels.querySelector('[data-role="channel"]:first-of-type)');
        if (firstChannel) {
            lastChannel.insertAdjacentElement('beforebegin', firstChannel);
            return;
        };

        groupChannels.append(category);
    },
    'response': () => { 
        console.log('response exists') 
    },

    'create_message': ({html, is_sender}) => {
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
    'delete_friendship': ({pk}) => {
        let friend = document.getElementById(`friend-${pk}`);
        decreaseCounter(friend.closest('.sidebar__section'));
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
    'edit_message': ({pk, content, is_mentioned, invites}) => {
        let backlog = document.getElementById(`backlog-${pk}`);
        if (!backlog) {
            return;
        };
        is_mentioned ? backlog.classList.add('backlog--mentioned') : backlog.classList.remove('backlog--mentioned');
        let backlogContent = backlog.querySelector('[data-role="content"]');
        backlogContent.innerHTML = content;

        let backlogInvites = backlog.querySelector('[data-role="invites"]');
        backlogInvites.innerHTML = invites;
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
        mentionableObserver.buildMentionablesList(html);
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
    'create_log': ({html, is_sender}) => {
        let newLog = parseHTML(html);
        let scrollbarWasAtBottom = scrollbarAtBottom(backlogs);
        backlogs.appendChild(newLog);
        
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
            backlogs.insertBefore(divider, newLog);
        };
    },
    'join_group_chat': ({html}) => {
        let insertGroupChat = document.getElementById('insert-group-chat');
        insertGroupChat.parentNode.insertBefore(parseHTML(html), insertGroupChat);
    },
    'leave_group_chat': ({pk}) => {
        let groupChat = document.getElementById(`group-chat-${pk}`);
        groupChat.remove();
    },
    'redirect': ({url}) => {
        window.location.replace(url);
    },
    'activate_private_chat': ({html}) => {
        let privateChats = document.getElementById('private-chats');
        privateChats.appendChild(parseHTML(html))
    },
    'build_emote_menu': (response) => {
        emoteMenuManager.buildEmoteMenu(response);
    },
};