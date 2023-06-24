import json
import re

from django.template import Template, Context
from django.template.defaulttags import register
from django.apps import apps
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.http import JsonResponse, HttpResponse
from django.contrib.contenttypes.models import ContentType



from rooms.models import Member, Room, Emote
from ..settings import MEDIA_URL
import utils

@register.filter(name='classname')
def classname(obj):
    return obj.__class__.__name__

@register.filter(name='eq')
def eq(self, other):
    return self == other

@register.filter(name="convert_reactions")
def convert_reactions(text, room_pk):
    room = Room.objects.get(pk=room_pk)
    pattern = r':(.*?):'
    def replace_with(match):
        name = match.group(1)
        try:
            reaction = Emote.objects.get(room=room, name=name)
            return f'<img src="{reaction.image.url}" alt="{reaction.name}">'
        except Emote.DoesNotExist:
            return match.group(0)


    return Template(re.sub(pattern, replace_with, text)).render(Context({}))
    

@register.filter(name="get_friendship_friend")
def get_friendship_friend(user, friendship):
    if user == friendship.receiver:
        return friendship.sender
    elif user == friendship.sender:
        return  friendship.receiver
    
@register.filter(name="attribute_modifier")
def attribute_modifier(obj, json_string):
    parsed_json = json.loads(json_string)
    attribute, success_string = parsed_json['attribute'], parsed_json['on_success']
    if getattr(obj, attribute, None):
        return success_string
    else:
        return ''


@register.filter(name="printInConsole")
def printInConsole(self):

    print(self)

    return self
    

@register.filter(name="get_member")
def get_member(user, room):
    return room.members.all().filter(user=user).first()


@register.filter(name="is_member")
def is_member(user, room):
    return room.pk in user.memberships.all().values_list('room', flat=True)


@register.filter(name='app_name')
def app_name(self):
    return self._meta.app_label


@register.filter(name='object_to_json')
def object_to_json(self):
    return json.dumps(utils.object_to_dict(self))


@register.filter(name='chain_arg')
def chain_arg(arg1, arg2):
    return arg1, arg2


@register.filter(name='member_has_role_perm')
def member_has_role_perm(member, codename):
    return utils.member_has_role_perm(member, codename)


@register.filter(name='member_has_channel_perm')
def member_has_channel_perm(args, codename=None):
    member, channel = args
    return utils.member_has_channel_perm(member, channel, codename)
