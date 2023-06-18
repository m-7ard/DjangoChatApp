from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission

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
    ModelPermission,
    ModelPermissionGroup
)
from users.models import CustomUser


class RoomForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self.instance, 'pk', None):
            self.fields['owner'].queryset = CustomUser.objects.filter(pk__in=self.instance.members.values_list('user'))


class RoomAdmin(admin.ModelAdmin):
    readonly_fields = ('default_role',)
    list_display = ('pk', 'name', 'description', 'owner')
    form = RoomForm


admin.site.register(Permission)
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
admin.site.register(ModelPermission)
admin.site.register(ModelPermissionGroup)