from django import forms
from .models import Room, Channel, Message, ChannelCategory, Action
from utils import get_object_or_none


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
    

class RoomForm(forms.ModelForm):
    image = forms.ImageField(required=True)

    class Meta:
        model = Room
        fields = ['name', 'description', 'image']
        
    def name(self):
        name = self.cleaned_data['name']
        if not name:
            raise forms.ValidationError('Room requires a name.')
        
        return name
        
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