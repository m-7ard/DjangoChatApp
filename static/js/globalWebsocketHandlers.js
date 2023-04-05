let chatSocketSendHandlers = {
	'ping':
		function(event) {
			console.log('pinged')
			chatSocket.send(JSON.stringify({
				'action': 'ping'
			}))
		},
	'requestServerResponse': 
		async () => {
			try {
				// send the ping message to the server
				await chatSocket.send(JSON.stringify({
				'action': 'requestServerResponse'
				}));
				console.log('requestServerResponse');
			} catch (error) {
				console.error('Error requestServerResponse', error);
			}
		},
};

let chatSocketReceiveHandlers = {
	'ping': chatSocketSendHandlers["ping"],
	'requestServerResponse': 
		function() {

		},
	'offline':
		function(data) {
			let user_references = document.querySelectorAll('')
		},
	'create-room': 
		function(data) {
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
	'remove-room':
		function(data) {
			if (window.location.href.includes('room/' + data.pk)) {
				window.location = "{% url 'dashboard' %}"
			};
			let roomReferences = [
				document.querySelector(`.app-section--sidebar__infobox[pk="${data.pk}"]`),
				// further room references...
			];
			roomReferences.forEach((element) => element.remove())
		},	
};