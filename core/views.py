import json
from urllib.parse import urlencode
from pathlib import Path


from django.shortcuts import render, redirect
from django.apps import apps
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, View
from django.urls import reverse
from django.utils.html import escape


from django.template import Template, RequestContext, Context
from django.http import HttpResponse
from django.forms import ModelForm
from django.template.loader import render_to_string

from users.models import Friendship, CustomUser
from rooms.models import Log, Message, Reaction, Room
from utils import get_object_or_none, dict_to_object

class FrontpageView(TemplateView):
    template_name = 'core/frontpage.html'


class RequestData(View):
    def get(self, request):
        app_label = request.GET.get('app_label')
        model_name = request.GET.get('model_name')
        pk = request.GET.get('pk')

        model = apps.get_model(app_label=app_label, model_name=model_name)
        instance = model.objects.get(pk=pk)

        keys = json.loads(request.GET.get('keys'))
        data = {
            'pk': escape(pk)
        }

        for key in keys:
            value = getattr(instance, key)
            if callable(value):
                data[key] = escape(value())
            else:
                data[key] = escape(value)
        
        return JsonResponse(data)
    

class GetTemplate(View):
    def get(self, request, *args, **kwargs):
        template_name = request.GET.get('template-name')
        client_context = json.loads(request.GET.get('context')) if request.GET.get('context') else {}
        objects = client_context.get('objects', {})
        variables = client_context.get('variables', {})
        
        template_context = {
            'client_context': request.GET.get('context'),
        }

        for context_variable, values in objects.items():
            template_context[context_variable] = dict_to_object(values)

        for context_variable, value in variables.items():
            template_context[context_variable] = value
        
        return HttpResponse(render_to_string(request=request, template_name=template_name, context=template_context))


def GetViewByName(request, name, *args, **kwargs):
    kwargs = json.loads(request.GET.get('kwargs')) if request.GET.get('kwargs') else {}
    query = json.loads(request.GET.get('query')) if request.GET.get('query') else {}
    url = reverse(name, kwargs=kwargs) + '?' + urlencode(query)

    return redirect(url)


