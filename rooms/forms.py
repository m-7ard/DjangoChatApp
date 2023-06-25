from django import forms
from .models import Room, Channel, Message, ChannelCategory, Action
from utils import get_object_or_none

from core.widgets import AvatarInput

class ChannelCreationForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'kind', 'order']


class ChannelDeleteForm(forms.ModelForm):
    confirm = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.fields['confirm'].label = f'I confirm that I wish to delete "{self.instance.name}"'

    class Meta:
        model = Channel
        fields = ['confirm']

class ChannelUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.fields['category'].queryset = self.instance.room.categories.all()
        self.fields['category'].selected = self.instance.category

    class Meta:
        model = Channel
        fields = ['name', 'description', 'order', 'category']
    

    


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