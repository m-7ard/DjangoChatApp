from django import forms
from .models import Channel
from utils import get_object_or_none
from datetime import datetime, timedelta, MAXYEAR

from core.widgets import AvatarInput
from commons import widgets
from .models import GroupChannel, GroupChat, Category

class ChannelCreateForm(forms.ModelForm):
    kind = forms.ChoiceField(widget=widgets.ChannelKindSelect(), choices=((),))
    name = forms.CharField(widget=widgets.FormTextInput())
    description = forms.CharField(widget=widgets.FormTextInput(), required=False)

    def __init__(self, category=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if category:
            self.fields['category'].initial = category.pk
            self.fields['category'].widget = self.fields['category'].hidden_widget()

    class Meta:
        model = GroupChannel
        fields = ['name', 'description', 'kind']


class ChannelDeleteForm(forms.ModelForm):
    confirm = forms.BooleanField(widget=widgets.FormSlider())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.fields['confirm'].label = f'I confirm that I wish to delete "{self.instance.name}"'
        self.fields['confirm'].widget.field = self.fields['confirm']

    class Meta:
        model = GroupChannel
        fields = ['confirm']

class ChannelUpdateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormTextInput())
    description = forms.CharField(widget=widgets.FormTextInput(), required=False)
    order =  forms.CharField(widget=widgets.FormNumberInput())
    category = forms.ModelChoiceField(widget=widgets.FormSelect(), queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = self.instance.room.categories.all()
        self.fields['category'].selected = self.instance.category
        self.fields['category'].widget.field = self.fields['category']

    class Meta:
        model = GroupChannel
        fields = ['name', 'description', 'order', 'category']


class ChannelPermissionsForm(forms.ModelForm):
    class Meta:
        model = GroupChannel
        fields = '__all__'
        

class GroupChatCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormTextInput())
    public = forms.BooleanField(widget=widgets.FormSlider(attrs={'label': 'List group chat as public?'}), label='', required=False)
    
    class Meta:
        model = GroupChat
        fields = ['name', 'public']


class GroupChannelCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormTextInput())
    
    class Meta:
        model = GroupChannel
        fields = ['name']


class CategoryCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormTextInput())
    
    class Meta:
        model = Category
        fields = ['name']


class FriendForm(forms.Form):
    username = forms.CharField()
    username_id = forms.IntegerField()


class InviteForm(forms.Form):
    one_time = forms.BooleanField(required=False)
    expiry_date = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expiry_date_values = {
            '1 day': lambda: datetime.today() + timedelta(days=1),
            '7 days': lambda: datetime.today() + timedelta(weeks=1),
            '30 days': lambda: datetime.today() + timedelta(days=30),
            '365 days': lambda: datetime.today() + timedelta(days=365),
            'forever': lambda: datetime.max
        }

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data["expiry_date"]
        if expiry_date not in self.expiry_date_values:
            raise forms.ValidationError("Not a valid expiry_date length")

        return self.expiry_date_values[expiry_date]()
    
"""
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
    pass

"""