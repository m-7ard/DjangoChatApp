import json
import re

from django.template import Template, Context
from django.template.defaulttags import register
from django.db.models import Q


from rooms.models import PrivateChat, BacklogGroupTracker
from users.models import Friendship


from ..settings import MEDIA_URL
import utils


@register.filter(name='classname')
def classname(obj):
    return obj.__class__.__name__


@register.filter(name="convert_mentions")
def convert_mentions(text):
    replace_with = lambda match: f'<span class="mention">{match.group(0)}</span>'
    return Template(re.sub(r'(?<!\w)>>(\w+#\d{2})(?!\w)', replace_with, text)).render(Context({}))


@register.filter(name="printInConsole")
def printInConsole(self):
    print(self)
    return self


@register.filter(name='chain_arg')
def chain_arg(arg1, arg2):
    return arg1, arg2


@register.filter(name='replaceWhitespace')
def split(string, replace_with='_'):
    return string.replace(' ', replace_with)


@register.filter(name="get_shared_private_chat")
def get_shared_private_chat(user1, user2):
    return (PrivateChat.objects.filter(memberships__user=user1) & PrivateChat.objects.filter(memberships__user=user2)).first()


@register.filter(name="unread_backlogs")
def unread_backlogs(user, backlog_group):
    tracker = BacklogGroupTracker.objects.filter(user=user, backlog_group=backlog_group).first()
    if not tracker.last_backlog_seen:
        return backlog_group.backlogs.filter(date_created__gt=tracker.last_updated)
        
    return backlog_group.backlogs.filter(date_created__gt=tracker.last_backlog_seen.date_created)


@register.filter(name="unread_group_channels")
def unread_group_chat_backlogs(user, group_chat):
    count = 0
    trackers = BacklogGroupTracker.objects.filter(user=user, backlog_group__in=group_chat.channels.values_list('backlog_group', flat=True))
    for tracker in trackers:
        count += tracker.unread_backlogs().count()

    return count


@register.filter(name="get_member_or_none")
def get_member_or_none(user, chat):
    return chat.memberships.filter(user=user).first()


@register.filter(name='get_friendship_or_none')
def get_friendship_or_none(user1, user2):
    return user1.friendships().intersection(user2.friendships()).first()