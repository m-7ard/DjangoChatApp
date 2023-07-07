from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission

from .models import (
    Room, 
    Channel, 
    Message, 
    Log, 
    Role, 
    Action, 
    Reaction, 
    Emote, 
    ChannelCategory,
    ChannelConfiguration,
    PrivateChat
)
from users.models import CustomUser



admin.site.register(Permission)
admin.site.register(Room)
admin.site.register(Channel)
admin.site.register(Message)
admin.site.register(Log)
admin.site.register(Role)
admin.site.register(Action)
admin.site.register(Reaction)
admin.site.register(Emote)
admin.site.register(ChannelCategory)
admin.site.register(ChannelConfiguration)
admin.site.register(PrivateChat)
