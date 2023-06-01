const tooltipCommandHandlers = {
    'manage-friendship': ({tooltip, trigger}) => {
        let {friendship, friend} = tooltipContext[tooltip.id];
        let friendshipPk = friendship.dataset.objectPk;
        let friendPk = friend.dataset.objectPk;
        let kind = trigger.dataset.kind;
        console.log(kind)

        chatSocketSendHandlers['manage-friendship']({
            friendshipPk: friendshipPk,
            friendPk: friendPk,
            kind: kind
        });
    },
    'profile': ({tooltip, trigger}) => {

    }
}