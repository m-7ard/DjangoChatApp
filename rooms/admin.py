from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission

from .models import (
    GroupChatMembership,
    PrivateChatMembership,
    GroupChat,
    Channel,
    Role

)

admin.site.register(GroupChat)
admin.site.register(Channel)
admin.site.register(Role)