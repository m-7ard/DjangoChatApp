from django.views.generic import TemplateView, DetailView, CreateView, View, FormView
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect
from django.urls import reverse
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseBadRequest

from core.models import News
from .models import Room, Channel, Log
from .forms import ChannelForm, RoomForm

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
                *list(self.object.room.logs.all().filter(action__in=self.object.display_logs.all()))
            ], key=lambda instance: instance.date_added)
        context['room'] = kwargs['object'].room
        return context


class ChannelCreateView(FormView):
    form_class = ChannelForm

    def form_valid(self, form):
        # Get the room object from the URL
        room_pk = self.kwargs['room']
        room = get_object_or_404(Room, pk=room_pk)
        
        # Set the room for the new channel
        channel = form.save(commit=False)
        channel.room = room
        channel.save()
        
        # Redirect back to the room
        return redirect('room', room=room_pk)
    
    def form_invalid(self, form):
        return HttpResponseBadRequest('Invalid Form Input')


class RoomCreateView(FormView):
    form_class = RoomForm

    def form_valid(self, form):
        room = form.save(commit=False)
        room.owner = self.request.user
        room.save()
        
        # Redirect back to the room
        return redirect('room', room=room.pk)
    
    def form_invalid(self, form):
        return HttpResponseBadRequest('Invalid Form Input')