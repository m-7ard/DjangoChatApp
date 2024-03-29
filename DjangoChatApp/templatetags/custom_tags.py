import json
import re

from django.template import Template, Context
from django.template.defaulttags import register
from django.db.models import Q


from rooms.models import PrivateChat, BacklogGroupTracker
from users.models import Friendship


from ..settings import MEDIA_URL


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


@register.filter(name="get_member_or_none")
def get_member_or_none(user, chat):
    return chat.memberships.filter(user=user).first()


@register.filter(name='get_friendship_or_none')
def get_friendship_or_none(user1, user2):
    return user1.get_friendships().intersection(user2.get_friendships()).first()


@register.filter('backlog_mentions_user')
def backlog_mentions_user(backlog, user):
    mentioned = user in backlog.user_mentions.all() 
    
    return mentioned


@register.filter('backlog_mentions_member_role')
def backlog_mentions_member_role(backlog, member):
    if not backlog.role_mentions.exists():
        return None
        
    return backlog.role_mentions.all().intersection(member.roles.all())


@register.filter('member_has_perm')
def member_has_perm(member, perm_name):
    return member.has_perm(perm_name)


@register.filter('backlog_mentions')
def backlog_mentions(backlog, user):
    """
    
    IDEA: instead of doing .get_roles which is just there
    to avoid a getattr error from PrivateChatMembership,
    we could just implement a regex check for >>all
    
    """
    if user in backlog.user_mentions.all():
        return True
    
    chat = backlog.get_chat()
    membership = chat.get_member(user.pk)
    if not membership:
        return False
    
    return membership.get_roles().intersection(backlog.role_mentions.all())


@register.filter('to_json')
def to_json(value):
    return json.dumps(value)


@register.filter('get_group_channel_notifications')
def get_group_channel_notifications(user, channel):
    member = channel.chat.get_member(user)
    tracker = BacklogGroupTracker.objects.get(user=user, backlog_group=channel.backlog_group)
    notifications_by_id = {"initial": {'unread_backlogs': 0, 'mentions': 0}}

    unread_backlogs = tracker.get_unread_backlogs()

    unread_backlog_count = unread_backlogs.count()
    mention_count = unread_backlogs.filter(Q(user_mentions=user) | Q(role_mentions__in=member.roles.all())).count()
    
    notifications_by_id[f"backlog-group-{tracker.backlog_group.pk}-unreads"] = unread_backlog_count
    notifications_by_id[f"backlog-group-{tracker.backlog_group.pk}-mentions"] = mention_count
    
    notifications_by_id["initial"]['unread_backlogs'] += unread_backlog_count
    notifications_by_id["initial"]['mentions'] += mention_count

    print(notifications_by_id)
    return notifications_by_id