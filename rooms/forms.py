from django import forms
from .models import Room, Channel, Message


class ChannelForm(forms.ModelForm):
	class Meta:
		model = Channel
		fields = ['name', 'description']


class RoomForm(forms.ModelForm):
	class Meta:
		model = Room
		fields = ['name', 'description']


class MessageForm(forms.ModelForm):
	class Meta:
		model = Message
		fields = ['content', 'user', 'channel', 'member']