from django import forms
from utils import get_object_or_none
from datetime import datetime, timedelta, MAXYEAR

from core.widgets import AvatarInput
from commons import widgets
from .models import GroupChannel, GroupChat, Category
from users.models import CustomUser


class GroupChatCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    public = forms.BooleanField(widget=widgets.FormLabeledSlider(attrs={'label': 'List group chat as public?'}), label='', required=False)
    
    class Meta:
        model = GroupChat
        fields = ['name', 'public']


class GroupChannelCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    
    class Meta:
        model = GroupChannel
        fields = ['name']


class CategoryCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    
    class Meta:
        model = Category
        fields = ['name']


class VerifyUser(forms.Form):
    username = forms.CharField()
    username_id = forms.IntegerField()

    def get_user(self):
        username = self.cleaned_data['username']
        username_id = self.cleaned_data['username_id']
        return get_object_or_none(CustomUser, username=username, username_id=username_id)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        username_id = cleaned_data.get('username_id')

        """

        TODO: make message actions like delete edit reacts

        """

        if not username or not username_id:
            return
        
        user = self.get_user()

        if not user:
            username_id = str(username_id).zfill(2)
            self.add_error(None, f'User {username}#{username_id} does not exist.')


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
