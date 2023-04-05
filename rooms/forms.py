from django import forms
from .models import Room, Channel, Message, ChannelCategory
from utils import get_object_or_none


class ChannelCreationForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'kind', 'category', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
class ChannelUpdateForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'order']

class RoomForm(forms.ModelForm):
    image = forms.ImageField(required=False)
        
    class Meta:
        model = Room
        fields = ['name', 'description', 'image']
        
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            return image
        else:
            return self.initial.get('image')

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'user', 'channel', 'member']