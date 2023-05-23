from django import forms
from .models import Room, Channel, Message, ChannelCategory, Action
from utils import get_object_or_none

from core.widgets import AvatarInput

class ChannelCreationForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'kind', 'order']
        

class ChannelEditForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'order']


class ChannelCategoryForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['category']
        

class ChannelPermissionsForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['display_logs']
        
    
class RoomCreationForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'description', 'image']
        
    def clean_image(self):
        image = self.cleaned_data.get('image')

        if image:
            return image
        else:
            # Keep the current image at the time of editing
            # if none provided
            return self.initial.get('image')
        

class RoomEditForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'description', 'image']
        
    def clean_image(self):
        image = self.cleaned_data.get('image')

        if image:
            return image
        else:
            # Keep the current image at the time of editing
            # if none provided
            return self.initial.get('image')

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'user', 'channel', 'member']