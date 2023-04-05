import json

from django.template.defaulttags import register
from django.apps import apps

from rooms.models import Member

@register.filter(name='user_is_member')
def user_is_member(user, room):
    return Member.objects.filter(user=user, room=room).first()

@register.filter(name='classname')
def classname(obj):
    return obj.__class__.__name__
