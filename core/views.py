import json

from django.shortcuts import render
from django.apps import apps
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, View
from django.urls import reverse


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
			'pk': pk
		}

		for key in keys:
			value = getattr(instance, key)
			data[key] = value
		
		return JsonResponse(data)
	

def get_reverse_url(request, name, *args, **kwargs):
	parameters = json.loads(request.GET.get('parameters'))
	return HttpResponse(reverse(name, kwargs=parameters))