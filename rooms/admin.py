from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission

from .models import (
    GroupChatMembership,
    PrivateChatMembership,
    GroupChat,
    PrivateChat,
    GroupChannel,
    Role,
    Category,
    Backlog,
    BacklogGroup,
    Message,
    Invite,
    BacklogGroupTracker,
    Emote,
    Reaction,
    Emoji,
    Log,
)

admin.site.register(GroupChat)
admin.site.register(PrivateChat)
admin.site.register(GroupChannel)
admin.site.register(Role)
admin.site.register(GroupChatMembership)
admin.site.register(PrivateChatMembership)
admin.site.register(Category)
admin.site.register(Backlog)
admin.site.register(BacklogGroup)
admin.site.register(Message)
admin.site.register(Log)
admin.site.register(Invite)
admin.site.register(BacklogGroupTracker)
admin.site.register(Emote)
admin.site.register(Reaction)
admin.site.register(Emoji)
