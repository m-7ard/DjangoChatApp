import asyncio
from pathlib import Path

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.template import Template, Context
from django.http import HttpResponse

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
    async_to_sync(channel_layer.group_send)(group_name, data)


def get_rendered_html(path, context_dict={}):
    with open(path, 'r') as f:
        html_string = f.read()

    template = Template(html_string)
    context = Context(context_dict)
    
    return template.render(context)