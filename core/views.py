import json
import os
from pathlib import Path


from django.shortcuts import render
from django.apps import apps
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, View
from django.urls import reverse
from django.utils.html import escape


from django.template import Template, RequestContext, Context
from django.http import HttpResponse


class FrontpageView(TemplateView):
    template_name = 'core/frontpage.html'


class RequestData(View):
    def get(self, request):
        app_label = request.GET.get('app_label')
        model_name = request.GET.get('model_name')
        pk = request.GET.get('pk')
        print(pk)

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
    

def get_reverse_url(request, name, *args, **kwargs):
    parameters = json.loads(request.GET.get('parameters'))
    return HttpResponse(reverse(name, kwargs=parameters))


class GetHtmlElementFromData(View):
    def get(self, request):
        app_label = request.GET.get('appLabel')
        template_route = request.GET.get('templateRoute')
        context_data = request.GET.get('contextData', {})
        element_path = Path().resolve().parent / app_label / template_route
        
        with open(element_path, 'r') as f:
            plain_html = f.read()
            
        template = Template(plain_html)
        context = Context(context_data)

        return HttpResponse(template.render(context))
    


class GetHtmlElementFromModel(View):
    def get(self, request):
        app_label = request.GET.get('appLabel')
        template_route = request.GET.get('templateRoute')
        context_data = request.GET.get('contextData', {})
        element_path = Path().resolve() / app_label / template_route
        model_name = request.GET.get('modelName')
        pk = request.GET.get('pk')
        context_variable = request.GET.get('contextVariable', 'object')

        model = apps.get_model(app_label=app_label, model_name=model_name)
        instance = model.objects.get(pk=pk)
        context_data[context_variable] = instance

        with open(element_path, 'r') as f:
            plain_html = f.read()
            
        template = Template(plain_html)
        context = Context(context_data)

        return HttpResponse(template.render(context))
    




