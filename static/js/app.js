window.addEventListener('load', () => {
	Object.assign(chatSocketSendHandlers, {
		'manage-friendship': function acceptOrRejectFriendRequestDB(event) {
			let trigger = event.target.closest('[data-command="manage_friendship"]');
			let friendshipPk = trigger.closest('.friendship, .tooltip').dataset.pk;
			let kind = trigger.dataset.kind;
			chatSocket.send(JSON.stringify({
				'action': 'manage_friendship',
				'kind': kind,
				'friendshipPk': friendshipPk,
			}));
		}
	});

	Object.assign(chatSocketReceiveHandlers, {
		'manage-friendship': function acceptOrRejectFriendRequestDOM(data) {
			let friend = document.querySelector(`.friendship[data-pk="${data.friendshipPk}"]`).closest('.modelbox');
			if (data.kind == 'accept') {
				let category = document.querySelector(`[data-friendship="${data.category}"]`);
				friend.querySelector('.friendship').innerHTML = `
				<div class="icon icon__hoverable icon--small offline-color--primary tooltip__trigger" 
				data-positioning='{"top": "100%", "right": "0px"}' 
				data-target=".friendship__menu">
					<i class="material-symbols-outlined">
						expand_more
					</i>
				</div>
				`;
				category.appendChild(friend);
			}
			else if (data.kind == 'reject' || data.kind == 'remove') {
				friend.remove();
			}
			
		}
	});

	Object.assign(commandHandlers, {
		'manage-friendship': chatSocketSendHandlers['manage-friendship'],
	});
});