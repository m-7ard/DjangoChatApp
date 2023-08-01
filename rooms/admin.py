from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission

from .models import (
    GroupChatMembership,
    PrivateChatMembership,
    GroupChat,
    PrivateChat,
    GroupChannel,
    PrivateChannel,
    Role,
    Category,
    Backlog,
    BacklogGroup,
    Message,
    Invite

)

admin.site.register(GroupChat)
admin.site.register(PrivateChat)
admin.site.register(PrivateChannel)
admin.site.register(GroupChannel)
admin.site.register(Role)
admin.site.register(GroupChatMembership)
admin.site.register(PrivateChatMembership)
admin.site.register(Category)
admin.site.register(Backlog)
admin.site.register(BacklogGroup)
admin.site.register(Message)
admin.site.register(Invite)