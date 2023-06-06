const processCommandEvent = {
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