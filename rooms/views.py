import os
import json
from itertools import chain
from typing import Any, Dict
from pathlib import Path

from django.db import models
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm

from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView, DeleteView, View
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseBadRequest, HttpResponse
from django.template import Template, RequestContext
from django.contrib import messages


from core.models import News
from .models import Room, Channel, Log, ChannelCategory, Action, Member
from .forms import (
    ChannelCreationForm,
    ChannelEditForm,
    ChannelCategoryForm,
    ChannelPermissionsForm, 
    RoomCreationForm,
    RoomEditForm,
)

from utils import get_object_or_none, send_to_group, get_rendered_html


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
        return Room.objects.get(pk=self.kwargs['room'])

class ChannelView(DetailView):
    template_name = 'rooms/channel.html'
    model = Channel
    context_object_name = 'channel'

    def get_object(self):
        return Channel.objects.get(pk=self.kwargs['channel'])

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel = self.object
        messages = channel.messages.all()
        logs = channel.room.logs.all().filter(action__in=channel.display_logs.all())

        context['backlogs'] = sorted(
            chain(messages, logs),
            key=lambda obj: obj.date_added
        )
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


class LeaveRoom(TemplateView):
    template_name = 'rooms/forms/leave-room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = Room.objects.get(pk=kwargs.get('room'))
        return context

    def post(self, request, *args, **kwargs):
        room = Room.objects.get(pk=kwargs.get('room'))
        user = request.user
        member = get_object_or_none(Member, room=room, user=user)
        if member:
            action = Action.objects.get(name='leave')
            log = Log.objects.create(action=action, receiver=user, room=room)
            context = {
                'object': log, 
                'room': room
            }
            log_html = get_rendered_html(
                path=Path(__file__).parent / 'templates/rooms/elements/log.html', 
                context_dict=context
            )

            member.delete()

            send_data = {
                'type': 'send_to_JS',
                'action': 'leave-room',
                'html': log_html,
            }
            for channel in room.channels.filter(display_logs=action):
                print(channel.pk, '------------------' * 20)
                send_to_group(f'channel_{channel.pk}', send_data)

        return redirect('room', room=room.pk)
    

class JoinRoom(View):
    def post(self, request, *args, **kwargs):
        room = Room.objects.get(pk=kwargs.get('room'))
        user = request.user
        member, created = Member.objects.get_or_create(room=room, user=user)

        if created:
            action = Action.objects.get(name='join')
            log = Log.objects.create(action=action, receiver=user, room=room)
            context = {
                'object': log, 
                'room': room
            }
            log_html = get_rendered_html(
                path=Path(__file__).parent / 'templates/rooms/elements/log.html', 
                context_dict=context
            )
            send_data = {
                'type': 'send_to_JS',
                'action': 'join-room',
                'html': log_html,
            }

            for channel in room.channels.filter(display_logs=action):
                send_to_group(f'channel_{channel.pk}', send_data)

        return redirect('room', room=room.pk)