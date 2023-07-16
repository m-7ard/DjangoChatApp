import datetime
from dateutil.relativedelta import relativedelta


from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.text import capfirst


from .models import CustomUser
from commons import widgets


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        widget=widgets.FormEmailInput()
    )
    birthday = forms.DateTimeField(
        label="Birthday", 
        required=True, 
        widget=widgets.FormDateInput(attrs={'type':'date'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=widgets.FormPasswordInput()
    )
    password2 = forms.CharField(
        label="Repeat password", 
        widget=widgets.FormPasswordInput(),
    )
    username = forms.CharField(
        max_length=30,
        widget=widgets.FormTextInput()
    )

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'username',
            'birthday',
            'password1',
            'password2',
        )

    def clean_birthday(self):
        birthday = self.cleaned_data['birthday']
        if birthday > datetime.datetime.now(datetime.timezone.utc) - relativedelta(years=13):
            raise forms.ValidationError('You must be at least 13 years old to register.')
        
        return birthday
        

class CustomisedAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=widgets.FormTextInput())
    password = forms.CharField(widget=widgets.FormPasswordInput())