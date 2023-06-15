from django.contrib import admin
from django import forms

from .models import (
    Room, 
    Channel, 
    Message, 
    Log, 
    Role, 
    Member, 
    Action, 
    Reaction, 
    Emote, 
    ChannelCategory,
    ChannelConfiguration,
)
from users.models import CustomUser

class RoomForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['default_role'].queryset = Role.objects.filter(room=self.instance)
        self.fields['owner'].queryset = CustomUser.objects.filter(pk__in=self.instance.members.values_list('user'))

class RoomAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'description', 'owner')
    form = RoomForm

admin.site.register(Room, RoomAdmin)
admin.site.register(Channel)
admin.site.register(Message)
admin.site.register(Log)
admin.site.register(Role)
admin.site.register(Member)
admin.site.register(Action)
admin.site.register(Reaction)
admin.site.register(Emote)
admin.site.register(ChannelCategory)
admin.site.register(ChannelConfiguration)
