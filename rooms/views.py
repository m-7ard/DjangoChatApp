from django.views.generic import TemplateView, DetailView

from core.models import News
from .models import Room, Channel, Log

from itertools import chain


class DashboardView(TemplateView):
	template_name = 'rooms/dashboard.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['site_news'] = News.objects.all()
		return context

class RoomView(DetailView):
	template_name = 'rooms/room.html'
	model = Room
	context_object_name = 'room'

	def get_object(self):
		return Room.objects.get(id=self.kwargs['room'])

class ChannelView(DetailView):
	template_name = 'rooms/channel.html'
	model = Channel
	context_object_name = 'channel'

	def get_object(self):
		return Channel.objects.get(id=self.kwargs['channel'])

	def dispatch(self, request, *args, **kwargs):
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['backlogs'] = sorted([
				*list(self.object.messages.all()),
				*list(Log.objects.all())
			], key=lambda instance: instance.date_added)
		print(context['backlogs'])
		context['room'] = kwargs['object'].room
		return context