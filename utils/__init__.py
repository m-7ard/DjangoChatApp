from pathlib import Path

from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render

channel_layer = get_channel_layer()


def get_object_or_none(obj, **kwargs):
    return obj.objects.filter(**kwargs).first()


def create_send_to_group(group_name, data):
    pass


def get_object_or_none(obj, **kwargs):
    return obj.objects.filter(**kwargs).first()


def send_to_group(group_name, data):
    try:
        async_to_sync(channel_layer.group_send)(group_name, data)
    except Exception as e:
        # There seems to be a redis race condition error when joining
        # a room through the explorer
        
        print(f'Exception occured in utils.send_to_group: {e}')


def get_rendered_html(template_path, request, context_dict={}):
    return render(request, template_path, context_dict)


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



