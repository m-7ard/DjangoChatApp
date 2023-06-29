import asyncio
import json
from pathlib import Path

from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.template import Template, Context
from django.http import HttpResponse
from django.template import loader

channel_layer = get_channel_layer()


def get_object_or_none(obj, **kwargs):
    return obj.objects.filter(**kwargs).first()


def create_send_to_group(group_name, data):
    async def send_to_group():
        await channel_layer.group_send(group_name, data)
    
    print('channel layer: ', channel_layer)
    sync_send_to_group = async_to_sync(send_to_group)
    
    return sync_send_to_group


def get_object_or_none(obj, **kwargs):
    return obj.objects.filter(**kwargs).first()


def send_to_group(group_name, data):
    try:
        async_to_sync(channel_layer.group_send)(group_name, data)
    except Exception as e:
        # There seems to be a redis race condition error when joining
        # a room through the explorer
        
        print(f'Exception occured in utils.send_to_group: {e}')


def get_rendered_html(template_path, context_dict={}):
    """
        template_path name needs to be in template_name format like app/.../template.html
        rather than using a path constructed using Path, os etc
    """ 
    template = loader.get_template(template_path)
    context = Context(context_dict)
    return template.render(context_dict)


def dict_to_object(json_dict):
    if not json_dict:
        return

    model_name = json_dict['model']
    app_label = json_dict['app']
    pk = json_dict['pk']
    model = apps.get_model(app_label=app_label, model_name=model_name)
    return get_object_or_none(model, pk=pk)


def object_to_dict(self):
    if not self:
        return
    
    parsed_object = {
        "pk": self.pk,
        "model": self.__class__.__name__,
        "app": self._meta.app_label
    }
    return parsed_object


def member_has_role_perm(member, codename):
    if not member:
        return False
    
    member_roles = sorted(member.roles.all(), key=lambda role: role.hierarchy)
    is_owner = member.user == member.room.owner
    is_admin = any([role.admin for role in member_roles])
    if is_admin or is_owner:
        return True
    
    for role in member_roles:
        role_permissions = role.permissions.items.all()
        value = role_permissions.get(permission__codename=codename).value
        if value != None:
            return value
    

def member_has_channel_perm(member, channel, codename):
    if not member:
        return False
    
    member_roles = sorted(member.roles.all(), key=lambda role: role.hierarchy)
    is_owner = member.user == member.room.owner
    is_admin = any([role.admin for role in member_roles])
    if is_admin or is_owner:
        return True

    channel_roles = sorted(channel.configs.all().filter(role__in=member_roles), key=lambda config: config.role.hierarchy)
    for role in channel_roles:
        role_permissions = role.permissions.items.all()
        value = role_permissions.get(permission__codename=codename).value
        if value != None:
            return value

    



