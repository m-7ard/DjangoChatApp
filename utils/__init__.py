import base64

from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import render
from django.core.files.base import ContentFile

channel_layer = get_channel_layer()

def get_object_or_none(obj, **kwargs):
    return obj.objects.filter(**kwargs).first()


def process_mention(mention):
    import re

    alphanumeric_pattern = r'>>([a-zA-Z0-9]+)'
    numeric_pattern = r'#(\d{1,2})?$'
    
    alphanumeric_match = re.search(alphanumeric_pattern, mention)
    numeric_match = re.search(numeric_pattern, mention)
    
    alphanumeric = alphanumeric_match.group(1) if alphanumeric_match else None
    numeric = numeric_match.group(1) if numeric_match else None
    
    return alphanumeric, numeric


def base64_file(data, name=None):
    _format, _img_str = data.split(';base64,')
    _name, ext = _format.split('/')
    if not name:
        name = _name.split(":")[-1]
    return ContentFile(base64.b64decode(_img_str), name='{}.{}'.format(name, ext))