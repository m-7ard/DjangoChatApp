from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

"""
use baseuser instead reminder
"""
class UserAttributes_SignupForm(UserCreationForm):
	email = forms.EmailField()

	class Meta:
		model = User
		fields = (
			'username',
			'email',
			'password1',
			'password2',
		)


class ProfileAttributes_SignupForm(forms.ModelForm):
	birthday = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
	
	class Meta:
		model = Profile
		fields = (
			'birthday',
		)
	
