window.addEventListener('load', () => {
	// DOM Elements
	let chatbarInput = document.querySelector('.chatbar__input');
	let appMessages = document.querySelector('#app-messages');
	
	// Scroll to bottom
	appMessages.scrollTo(0, appMessages.scrollHeight);

	// Chatbar enter listener
	chatbarInput.addEventListener('keypress', chatSocketSendHandlers['send-message'])
});