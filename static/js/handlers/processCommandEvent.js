const processCommandEvent = {
    'manage-friendship': (event) => {
        let friendship = event.target.closest('[data-object-type="friendship"]');
        let friend = event.target.closest('[data-object-type="friend"]');
        let trigger = event.target.closest('[data-command="manage-friendship"]');
        let args = {
            friendshipPk: friendship.dataset.objectPk,
            friendPk: friend.dataset.objectPk,
            kind: trigger.dataset.kind
        };
        return args;
    },
    'react': (event) => {
        let emote = event.target.closest('.reaction');
        let object = event.target.closest('[data-object-type]');
        let args = {
            objectType: object.dataset.objectType,
            objectPk: object.dataset.objectPk,
            emotePk: emote.dataset.emotePk
        };
        return args;
    },
    'edit-message': (event) => {
        let message = event.target.closest('[data-object-type="message"]');
        let args = {
            message: message,
        };
        return args;
    },
    'delete-backlog': (event) => {
        let object = event.target.closest('.backlog');
        let args = {
            objectType: object.dataset.objectType,
            objectPk: object.dataset.objectPk,
        };
        return args;
    },
}