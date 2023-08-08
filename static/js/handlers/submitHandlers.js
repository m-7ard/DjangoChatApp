const submitHandlers = {
    'process-form': async (event) => await processForm(event),
    'create-invite': async (event) => {
        let invite = document.getElementById('invite-link');
        let form = event.target.closest('form');
        let request = await fetch(form.action, {
            method: form.method,
            body: new FormData(form)
        });
        let response = await request.json();

        if (response.status == '200') {
            invite.value = window.origin + response.invite_link;
        }
        else if (response.status == '400') {
            invite.value = 'Could not generate invite';
        };
    },
    'accept-invite': async (event) => {
        let form = event.target.closest('form');
        let request = await fetch(form.action, {
            method: form.method,
            body: new FormData(form)
        });
        let response = await request.json();

        if (response.status == 200) {
            window.location.replace(response.redirect);
        }
        else if (response.status == 400) {
            let button = form.querySelector('[data-role="accept-invite"]');
            button.classList.replace('invite__button--accept', 'invite__button--expired');
            button.disabled = true;
            button.textContent = 'Invite Already Expired';
        };
    }
}