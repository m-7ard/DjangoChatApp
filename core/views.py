import json
import urllib.parse
from pathlib import Path


from django.shortcuts import render, redirect
from django.apps import apps
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, View
from django.urls import reverse
from django.utils.html import escape


from django.template import Template, RequestContext, Context
from django.http import HttpResponse


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
        
        
def GetViewByName(request, name, *args, **kwargs):
    # parameters, as in .../room/<int:room>/ url parameters
    parameters = request.GET.get('parameters', {})
    get_data = request.GET.get('getData', {})


    if parameters:
        parameters = json.loads(parameters)

    if get_data:
        get_data = json.loads(get_data)
        get_data = urllib.parse.urlencode(get_data)

    url = reverse(name, kwargs=parameters)
    url += f'?{get_data}'

    return redirect(url)


class GetHtmlElementFromData(View):
    """ 
    Both GetHtmlElementFromData and GetHtmlElementFromModel retrieve a
    html element given an app label and element path;
    GetHtmlElementFromData will however populate it with the manually
    provided data, while GetHtmlElementFromModel will populate it with
    model data, by passing it as a context variable.
    """
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
    """
    GetHtmlElementFromModel will populate the element with
    model data, by passing it as a context variable. Requires
    a pk, app label and model name.
    """
    def get(self, request):
        app_label = request.GET.get('appLabel')
        template_route = request.GET.get('templateRoute')
        context_data = json.loads(request.GET.get('contextData', '{}'))
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
    




