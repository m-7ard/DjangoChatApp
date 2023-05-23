import os
import json
from typing import Any, Optional

from django.db import models
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm

from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView, DeleteView
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseBadRequest, HttpResponse
from django.template import Template, RequestContext
from django.contrib import messages


from core.models import News
from .models import Room, Channel, Log, ChannelCategory, Action
from .forms import (
    ChannelCreationForm,
    ChannelEditForm,
    ChannelCategoryForm,
    ChannelPermissionsForm, 
    RoomCreationForm,
    RoomEditForm,
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


class ChannelUpdateView(TemplateView):
    template_name = 'rooms/forms/update-channel.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        channel = Channel.objects.get(pk=kwargs['channel'])
        context['category'] = channel.category
        context['channel'] = channel
        context['actions'] = Action.objects.all()
        context['ChannelEditForm'] = ChannelEditForm(instance=channel)
        context['ChannelCategoryForm'] = ChannelCategoryForm(instance=channel)
        context['ChannelPermissionsForm'] = ChannelPermissionsForm(instance=channel)
        
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        form_name = request.POST.get('form')
        if form_name == 'ChannelEditForm':
            form = ChannelEditForm
        elif form_name == 'ChannelCategoryForm':
            form = ChannelCategoryForm
        elif form_name == 'ChannelPermissionsForm':
            form = ChannelPermissionsForm
        
        channel_form = form(
            instance=Channel.objects.get(pk=kwargs['channel']),
            data=request.POST
        )

        if channel_form.is_valid():
            channel = channel_form.save(commit=False)
            if form_name == 'ChannelPermissionsForm':
                channel.display_logs.set(Action.objects.filter(pk__in=request.POST.getlist('display_logs')))

            channel.save()

            return redirect('channel', room=channel.room.pk, channel=channel.pk)

        return redirect('dashboard')


class ChannelDeleteView(DeleteView):
    model = Channel

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        channel = self.kwargs.get('channel')

        return queryset.get(pk=channel)

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        super().delete(*args, **kwargs)
        
    def get_success_url(self):
        return reverse('room', kwargs={'room': self.object.room.pk})


class RoomCreateView(FormView):
    form_class = RoomCreationForm
    template_name = 'rooms/forms/create-room.html'
    
    def post(self, request, *args, **kwargs):
        room_form = RoomCreationForm(data=request.POST, files=request.FILES)
        if room_form.is_valid():
            room = room_form.save(commit=False)
            room.owner = request.user
            room.save()
            return redirect('room', room=room.pk)
        
        return render(request, self.template_name, {'form': room_form})
    

class RoomUpdateView(TemplateView):
    template_name = 'rooms/forms/update-room.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        room = Room.objects.get(pk=kwargs['room'])
        context['room'] = room
        context['RoomEditForm'] = RoomEditForm(instance=room)
        
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        form_name = request.POST.get('form')
        if form_name == 'RoomEditForm':
            form = RoomEditForm
        
        room_form = form(
            instance=Room.objects.get(pk=kwargs['room']),
            data=request.POST,
            files=request.FILES
        )

        if room_form.is_valid():
            room = room_form.save()

            return redirect('room', room=room.pk)
    
    
def get_html_form(request, form_name, *args, **kwargs):
    form_path = os.path.join('rooms', 'templates', 'rooms', 'forms', form_name)
    
    with open(form_path, 'r') as f:
        form = f.read()
        
    form = Template(form)
    context = RequestContext(request, request.GET)

    return HttpResponse(form.render(context))