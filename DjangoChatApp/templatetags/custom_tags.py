import json
import re

from django.template import Template, Context
from django.template.defaulttags import register



from ..settings import MEDIA_URL
import utils

@register.filter(name='classname')
def classname(obj):
    return obj.__class__.__name__

@register.filter(name='eq')
def eq(self, other):
    return self == other

"""
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
"""


@register.filter(name="printInConsole")
def printInConsole(self):
    return self


@register.filter(name='app_name')
def app_name(self):
    return self._meta.app_label


@register.filter(name='object_to_json')
def object_to_json(self):
    return json.dumps(utils.object_to_dict(self))


@register.filter(name='chain_arg')
def chain_arg(arg1, arg2):
    return arg1, arg2


@register.filter(name='split')
def split(string, split_at=' '):
    return string.split(split_at)


@register.filter(name='replaceWhitespace')
def split(string, replace_with='_'):
    return string.replace(' ', replace_with)


@register.filter(name="generateID")
def generateID(self):
    return f'{app_name(self)}-{classname(self)}-{self.pk}'
