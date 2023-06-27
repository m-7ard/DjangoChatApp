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

from users.models import Friendship, CustomUser
from rooms.models import Log, Message, Reaction, Room
from utils import get_rendered_html, get_object_or_none, dict_to_object

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
    

class GetTooltip(View):
    def get(self, request, *args, **kwargs):
        tooltip_id = kwargs.get('id')
        client_context = json.loads(request.GET.get('context')) if request.GET.get('context') else {}
        objects = client_context.get('objects', {})
        variables = client_context.get('variables', {})
        
        template_context = {
            'client_context': request.GET.get('context'),
            'user': request.user
        }

        for context_variable, values in objects.items():
            template_context[context_variable] = dict_to_object(values)

        for context_variable, value in variables.items():
            template_context[context_variable] = value

        html = get_rendered_html(
            path=Path(__file__).parent / f'templates/core/tooltips/{tooltip_id}.html', 
            context_dict=template_context
        )
        return HttpResponse(html)
    

class GetOverlay(View):
    def get(self, request, *args, **kwargs):
        overlay_id = kwargs.get('id')
        client_context = json.loads(request.GET.get('context')) if request.GET.get('context') else {}
        objects = client_context.get('objects', {})
        variables = client_context.get('variables', {})
        
        template_context = {
            'client_context': request.GET.get('context'),
            'user': request.user
        }

        for context_variable, values in objects.items():
            template_context[context_variable] = dict_to_object(values)

        for context_variable, value in variables.items():
            template_context[context_variable] = value

        return render(request, Path(__file__).parent / f'templates/core/overlays/{overlay_id}.html', context=template_context) 


def _(request, *args, **kwargs):
    client_context = json.loads(request.GET.get('context')) if request.GET.get('context') else {}
    forms = client_context.get('forms', {})
    if not forms:
        return
    
    template_context = {
        'client_context': request.GET.get('context'),
        'user': request.user,
        'forms': []
    }
    for form in forms:
        model_name = form.get('model')
        app_label = form.get('app')
        pk = form.get('pk')
        fields = form.get('fields')
        model = apps.get_model(app_label=app_label, model_name=model_name)

        class Form(ModelForm):
            nonlocal model
            nonlocal fields   

            class Meta:
                model = None
                fields = None
            
            Meta.model = model
            Meta.fields = fields

        title = form.get('title')
        subtitle = form.get('subtitle')
        
        template_context['forms'].append({
            'title': title,
            'subtitle': subtitle,
            'fields': Form(instance=get_object_or_none(model, pk=pk))
        })

    return render(request, 'core/dynamic-form.html', context=template_context)



def GetViewByName(request, name, *args, **kwargs):
    kwargs = json.loads(request.GET.get('kwargs')) if request.GET.get('kwargs') else {}
    query = json.loads(request.GET.get('query')) if request.GET.get('query') else {}
    url = reverse(name, kwargs=kwargs) + '?' + urlencode(query)

    return redirect(url)


