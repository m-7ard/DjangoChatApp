import re
from datetime import datetime, timedelta, MAXYEAR

from django import forms
from django.core.validators import RegexValidator, BaseValidator

from commons import widgets
from .models import GroupChannel, GroupChat, Category, Emote, Invite, Role
from users.models import CustomUser
from utils import get_object_or_none


class GroupChatCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    public = forms.BooleanField(widget=widgets.FormSlider(), required=False)
    
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
    user = forms.CharField(
        widget=widgets.FormInput,
        validators=[RegexValidator(r'^[a-zA-Z0-9]+#\d{2}$', 'Please enter a valid user (e.g. user#00)')]
    )

    def get_user(self):
        username, username_id = self.cleaned_data['user'].split('#')
        return get_object_or_none(CustomUser, username=username, username_id=username_id)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('user'):
            return
        
        user = self.get_user()

        if not user:
            user = cleaned_data['user']
            self.add_error('user', f'User {user} does not exist.')


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


class RoleCreateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    color = forms.CharField(widget=widgets.FormColorPicker())
    can_create_messages = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_messages = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_react = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_channels = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_chat = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_mention_all = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_kick_members = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_ban_members = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_create_invites = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_get_invites = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_invites = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_emotes = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_roles = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_see_channels = forms.ModelMultipleChoiceField(widget=widgets.FormPillMutliselect(), queryset=None, required=False)
    can_use_channels = forms.ModelMultipleChoiceField(widget=widgets.FormPillMutliselect(), queryset=None, required=False)


    class Meta:
        fields = [
            "name",
            "color",
            "can_see_channels",
            "can_use_channels",
            "can_create_messages",
            "can_manage_messages",
            "can_react",
            "can_manage_channels",
            "can_manage_chat",
            "can_mention_all",
            "can_kick_members",
            "can_ban_members",
            "can_create_invites",
            "can_get_invites",
            "can_manage_invites",
            "can_manage_emotes",
            "can_manage_roles"
        ]
        model = Role


class RoleUpdateForm(forms.ModelForm):
    name = forms.CharField(widget=widgets.FormInput())
    color = forms.CharField(widget=widgets.FormColorPicker())
    can_create_messages = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_messages = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_react = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_channels = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_chat = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_mention_all = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_kick_members = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_ban_members = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_create_invites = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_get_invites = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_invites = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_emotes = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_manage_roles = forms.IntegerField(widget=widgets.FormTriStateSwitch(), initial=0)
    can_see_channels = forms.ModelMultipleChoiceField(widget=widgets.FormPillMutliselect(), queryset=None, required=False)
    can_use_channels = forms.ModelMultipleChoiceField(widget=widgets.FormPillMutliselect(), queryset=None, required=False)

    class Meta:
        fields = [
            "name",
            "color",
            "can_see_channels",
            "can_use_channels",
            "can_create_messages",
            "can_manage_messages",
            "can_react",
            "can_manage_channels",
            "can_manage_chat",
            "can_mention_all",
            "can_kick_members",
            "can_ban_members",
            "can_create_invites",
            "can_get_invites",
            "can_manage_invites",
            "can_manage_emotes",
            "can_manage_roles"
        ]
        model = Role

    def clean_name(self):
        name = self.cleaned_data['name']
        if name == self.instance.name:
            return name
        
        if name in self.instance.chat.roles.values_list('name', flat=True):
            raise forms.ValidationError(f'Role with name "{name}" already exists.')

        return name


class BaseRoleUpdateForm(forms.ModelForm):
    color = forms.CharField(widget=widgets.FormColorPicker())
    can_create_messages = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_manage_messages = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_react = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_manage_channels = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_manage_chat = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_mention_all = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_kick_members = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_ban_members = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_create_invites = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_get_invites = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_manage_invites = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_manage_emotes = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_manage_roles = forms.ChoiceField(widget=widgets.FormBiStateSwitch(), choices=((1, True), (-1, False)))
    can_see_channels = forms.ModelMultipleChoiceField(widget=widgets.FormPillMutliselect(), queryset=None, required=False)
    can_use_channels = forms.ModelMultipleChoiceField(widget=widgets.FormPillMutliselect(), queryset=None, required=False)

    class Meta:
        fields = [
            "color",
            "can_see_channels",
            "can_use_channels",
            "can_create_messages",
            "can_manage_messages",
            "can_react",
            "can_manage_channels",
            "can_manage_chat",
            "can_mention_all",
            "can_kick_members",
            "can_ban_members",
            "can_create_invites",
            "can_get_invites",
            "can_manage_invites",
            "can_manage_emotes",
            "can_manage_roles"
        ]
        model = Role


class RoleManageMembersForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(widget=widgets.FormCheckboxMutliselect(), queryset=None, required=False)

    class Meta:
        fields = ['members']
        model = Role