const submitHandlers = {
    'process-form': async (event) => {
        let form = event.target.closest('form');
        let request = await fetch(form.action, {
            method: form.method,
            body: new FormData(form)
        });
        let response = await request.json();
        // Remove old messages
        form.querySelectorAll('.form__message').forEach((message) => message.remove());

        if (response.redirect) {
            window.location.replace(response.redirect);
        };
    
        if (response.status == 200) {
            // Success
            quickCreateElement('div', {
                classList: ['form__message', 'form__message--confirmation'],
                innerHTML: response.confirmation,
                parent: form
            });
        }
        else if (response.status == 400) {
            // Error
    
            Object.entries(response.errors).forEach(([fieldName, errorList]) => {
                let field = form.querySelector(`[data-name="${fieldName}"]`);
                let parent = field ? field : form;

                errorList.forEach((error) => {
                    let {code, message} = error;
                    quickCreateElement('div', {
                        classList: ['form__message', 'form__message--error'],
                        innerHTML: message,
                        parent: parent
                    });
                });
            });
        };
    }
}