import datetime
from dateutil.relativedelta import relativedelta


from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, CustomUser


class SignupForm(UserCreationForm):
    email = forms.EmailField()
    birthday = forms.DateTimeField(
        label="Birthday", 
        required=True, 
        widget=forms.NumberInput(attrs={'type':'date'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Repeat password", 
        widget=forms.PasswordInput,
    )
    username = forms.CharField(
        max_length=30,
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
        
        
                