from django import forms
from .models import Room, Channel, Message, ChannelCategory, Action
from utils import get_object_or_none

from core.widgets import AvatarInput
from commons.widgets import (
    ChannelKindSelect, 
    FormTextInput, 
    FormNumberInput, 
    FormSelect,
    FormCheckbox,
)
from .models import Channel

class ChannelCreateForm(forms.ModelForm):
    kind = forms.ChoiceField(widget=ChannelKindSelect(), choices=Channel.KIND)
    name = forms.CharField(widget=FormTextInput())
    description = forms.CharField(widget=FormTextInput())

    def __init__(self, category=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if category:
            self.fields['category'].initial = category.pk
            self.fields['category'].widget = self.fields['category'].hidden_widget()

    class Meta:
        model = Channel
        fields = ['name', 'description', 'kind', 'category']


class ChannelDeleteForm(forms.ModelForm):
    confirm = forms.BooleanField(widget=FormCheckbox())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.fields['confirm'].label = f'I confirm that I wish to delete "{self.instance.name}"'
        self.fields['confirm'].widget.field = self.fields['confirm']

    class Meta:
        model = Channel
        fields = ['confirm']

class ChannelUpdateForm(forms.ModelForm):
    name = forms.CharField(widget=FormTextInput())
    description = forms.CharField(widget=FormTextInput())
    order =  forms.CharField(widget=FormNumberInput())
    category = forms.ModelChoiceField(widget=FormSelect(), queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = self.instance.room.categories.all()
        self.fields['category'].selected = self.instance.category
        self.fields['category'].widget.field = self.fields['category']

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
        

class RoomUpdateForm(forms.ModelForm):
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