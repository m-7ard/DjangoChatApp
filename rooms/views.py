import os
from pathlib import Path
from typing import Any, Dict, Optional, Type
from django.db import models
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm

from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseBadRequest, HttpResponse
from django.template import Template, RequestContext
from django.contrib import messages

from core.models import News
from .models import Room, Channel, Log, ChannelCategory
from .forms import (
    ChannelCreationForm,
    ChannelEditForm, 
    RoomForm
)

from utils import get_object_or_none


class DashboardView(TemplateView):
    template_name = 'rooms/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['news'] = News.objects.all()
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


class Alternative_ChannelCreateView(CreateView):
    form_class = ChannelCreationForm
    model = Channel
    template_name = 'rooms/forms/create-channel.html'
    
    def form_valid(self, form):
        form.instance.room = Room.objects.get(pk=self.kwargs['room'])
        form.instance.category = get_object_or_none(ChannelCategory, pk=self.request.POST.get('category'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.request.GET.get('category')
        context['room'] = self.kwargs.get('room')
        return context

    def get_success_url(self):
        return reverse('channel', kwargs={'room': self.object.room.pk, 'channel': self.object.pk})



class ChannelCreateView(FormView):
    form_class = ChannelCreationForm
    template_name = 'rooms/forms/create-channel.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['category'] = get_object_or_none(ChannelCategory, pk=request.GET.get('category'))
        context['title'] = 'Create Channel'
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        channel_form = ChannelCreationForm(data=request.POST)

        if channel_form.is_valid():
            channel = channel_form.save(commit=False)
            channel.room = Room.objects.get(pk=kwargs['room'])
            channel.category = get_object_or_none(ChannelCategory, pk=request.POST.get('category'))
            channel.save()
                
            return redirect('channel', room=channel.room.pk, channel=channel.pk)
        
        messages.add_message(request, messages.ERROR, 'Something went wrong.')
        return redirect('dashboard')


class ChannelEditView(UpdateView):
    form_class = ChannelEditForm
    model = Channel
    template_name = 'rooms/forms/edit-channel.html'

    def get_object(self, queryset=None):
        return get_object_or_none(Channel, pk=self.kwargs.get('channel'))
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        context['title'] = 'Edit Channel'
        return self.render_to_response(context)
    
    def get_success_url(self):
        return reverse('channel', kwargs={'room': self.object.room.pk, 'channel': self.object.pk})

"""
TODO: 3 Forms in 1 for the channel updating
"""


class ChannelCategoryView(UpdateView):
    form_class = ChannelEditForm
    model = Channel
    template_name = 'rooms/forms/update-channel.html'

    def get_object(self, queryset=None):
        return get_object_or_none(Channel, pk=self.kwargs.get('channel'))
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        context['title'] = 'Edit Channel'
        return self.render_to_response(context)


class RoomCreateView(FormView):
    form_class = RoomForm
    template_name = 'rooms/forms/create-room.html'
    
    def post(self, request, *args, **kwargs):
        room_form = RoomForm(data=request.POST, files=request.FILES)
        if room_form.is_valid():
            room = room_form.save(commit=False)
            room.owner = request.user
            room.save()
            return redirect('room', room=room.pk)
        
        return render(request, self.template_name, {'form': room_form})
    

class RoomUpdateView(FormView):
    form_class = RoomForm

    def get_form(self):
        room = Room.objects.get(pk=self.kwargs['room'])
        return self.form_class(instance=room, data=self.request.POST)

    def form_valid(self, form):
        room = form.save()
        return redirect('room', room=room.pk)
    
    def form_invalid(self, form):
        return HttpResponseBadRequest('Invalid Form Input')
    
    
def get_html_form(request, form_name, *args, **kwargs):
    form_path = os.path.join('rooms', 'templates', 'rooms', 'forms', form_name)
    
    with open(form_path, 'r') as f:
        form = f.read()
        
    form = Template(form)
    context = RequestContext(request, request.GET)

    return HttpResponse(form.render(context))