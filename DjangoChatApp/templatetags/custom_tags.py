import json
import re

from django.template import Template, Context
from django.template.defaulttags import register
from django.apps import apps
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.http import JsonResponse, HttpResponse



from rooms.models import Member, Room, Reaction
from ..settings import MEDIA_URL

@register.filter(name='user_is_member')
def user_is_member(user, room):
    return Member.objects.filter(user=user, room=room).first()

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
            reaction = Reaction.objects.get(room=room, name=name)
            return f'<img src="{reaction.image.url}" alt="{reaction.name}">'
        except Reaction.DoesNotExist:
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
    
@register.filter(name="equality_modifier")
def equality_modifier(unpackable, string):
    self, other = unpackable
    if self == other:
        return string
    else:
        return ''
    
@register.filter(name="add_argument")
def add_argument(self, other):
    return self, other

@register.filter(name="printInConsole")
def printInConsole(self):
    print(self)
    
@register.filter(name="is_member")
def is_member(user, room):
    return room.pk in user.memberships.all().values_list('room', flat=True)
    