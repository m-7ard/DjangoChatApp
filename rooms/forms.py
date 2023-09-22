from django import forms
from utils import get_object_or_none
from datetime import datetime, timedelta, MAXYEAR

from commons import widgets
from .models import GroupChannel, GroupChat, Category, Emote, Invite
from users.models import CustomUser


class GroupChatCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    public = forms.BooleanField(widget=widgets.FormSlider(attrs={'label': 'List group chat as public?'}), label='', required=False)
    
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


class InviteForm(forms.ModelForm):
    expiry_date = forms.ChoiceField(choices=Invite.CHOICES, widget=widgets.FormSelect(attrs={'choices': Invite.CHOICES, 'initial': ('1 day', '1 Day')}))
    one_time = forms.BooleanField(required=False, widget=widgets.FormSlider())

    class Meta:
        model = Invite
        fields = ['expiry_date', 'one_time']

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


class EmoteCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    image = forms.ImageField(widget=widgets.FormImageInput())

    class Meta:
        model = Emote
        fields = ['name', 'image']


class EmoteUpdateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())

    class Meta:
        model = Emote
        fields = ['name']


class GroupChatLeaveForm(forms.Form):
    confirm = forms.BooleanField(required=True, label='Are you sure you wish to leave?', widget=widgets.FormSlider())