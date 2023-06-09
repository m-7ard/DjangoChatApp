import asyncio
import json
from pathlib import Path

from django.apps import apps
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


def json_to_object(json_dict):
    model_name = json_dict['model']
    app_label = json_dict['app']
    pk = json_dict['pk']
    model = apps.get_model(app_label=app_label, model_name=model_name)
    return get_object_or_none(model, pk=pk)

def object_to_json(self):
    json_dict = {
        "pk": self.pk,
        "model": self.__class__.__name__,
        "app": self._meta.app_label
    }
    # json.dumps, so the result uses double quotes
    return json.dumps(json_dict)