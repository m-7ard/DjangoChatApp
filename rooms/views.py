import os
import json
from itertools import chain
from typing import Any, Dict
from pathlib import Path

from django.db import models
from django.db.models.query import QuerySet
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm

from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView, DeleteView, View, ListView
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse 
from django.template import Template, RequestContext
from django.contrib import messages


from core.models import News
from .models import Room, Channel, Log, ChannelCategory, Action, Member, Message, ModelPermission
from .forms import (
    ChannelCreateForm,
    ChannelUpdateForm,
    ChannelPermissionsForm, 
    RoomCreationForm,
    RoomUpdateForm,
    ChannelDeleteForm,
)

from utils import (
    get_object_or_none, 
    send_to_group, 
    get_rendered_html,
    member_has_role_perm,
    member_has_channel_perm,
)


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.object
        member = get_object_or_none(Member, room=room, user=self.request.user)
        context['member'] = member
        return context

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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        channel = self.object
        member = get_object_or_none(Member, room=channel.room, user=self.request.user)
        messages = channel.messages.all()
        logs = channel.room.logs.all().filter(action__in=channel.display_logs.all())

        if not member:
            return redirect('room', room=channel.room.pk)

        can_view_messages = (
            member_has_role_perm(member, 'view_channel') 
            and member_has_channel_perm(member, channel, 'view_channel')
        )
        messages = messages if can_view_messages else messages.filter(member=member)

        context.update({
            'backlogs': sorted(chain(messages, logs), key=lambda obj: obj.date_added), 
            'room': channel.room,
            'member': member,
        })
        
        return self.render_to_response(context)


class ChannelCreateView(CreateView):
    form_class = ChannelCreateForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        category_pk = request.GET.get('category')
        category = ChannelCategory.objects.get(pk=category_pk) if category_pk else None
        context = self.get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Channel',
            'subtitle': category and category.name,
            'fields': ChannelCreateForm(category=category),
            'url': reverse('create-channel', kwargs={'pk': kwargs.get('pk')}),
            'type': 'create'
        }
        
        return render(request, self.template_name, context=context)
    
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        channel = form.save(commit=False)
        channel.room = Room.objects.get(pk=self.kwargs.get('pk'))
        channel.save()
        success_url = reverse('channel', kwargs={'channel': channel.pk, 'room': channel.room.pk})
        return JsonResponse({'status': 400, 'redirect': success_url})

class RoomManageView(TemplateView):
    template_name = 'commons/forms/full-dynamic-form.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        room = Room.objects.get(pk=kwargs['pk'])
        context['forms'] = [
            {
                'title': 'Update Room',
                'subtitle': room.name,
                'fields': RoomUpdateForm(),
                'url': reverse('update-room', kwargs={'pk': room.pk}),
                'type': 'update'
            },
        ]
    
        return render(request, self.template_name, context=context)


class ChannelManageView(TemplateView):
    template_name = 'commons/forms/full-dynamic-form.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        channel = Channel.objects.get(pk=kwargs['pk'])
        context['forms'] = [
            {
                'title': 'Update Channel',
                'subtitle': channel.category and channel.category.name,
                'fields': ChannelUpdateForm(instance=channel),
                'url': reverse('update-channel', kwargs={'pk': channel.pk}),
                'type': 'update'
            },
            {
                'title': 'Delete Channel',
                'subtitle': channel.category and channel.category.name,
                'warning': 'This action is not reversible',
                'fields': ChannelDeleteForm(instance=channel),
                'url': reverse('delete-channel', kwargs={'pk': channel.pk}),
                'type': 'delete'
            },
        ]
        
        return render(request, self.template_name, context=context)


class ChannelUpdateView(UpdateView):
    model = Channel
    form_class = ChannelUpdateForm

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'status': 200})
        

class ChannelDeleteView(DeleteView):
    model = Channel
    form_class = ChannelDeleteForm

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data(), 'message': 'Could not delete channel'})

    def form_valid(self, form):
        success_url = reverse('room', kwargs={'room': self.object.room.pk})
        self.object.delete()
        return JsonResponse({'status': 400, 'redirect': success_url})
    

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
    

class RoomUpdateView(UpdateView):
    model = Room

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'status': 400})


class LeaveRoom(TemplateView):
    template_name = 'rooms/forms/leave-room.html'

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
                send_to_group(f'channel_{channel.pk}', send_data)

        return redirect('room', room=room.pk)
    

class DeleteRoom(DeleteView):
    model = Room

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        room = self.kwargs.get('room')
        return queryset.get(pk=room)

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        super().delete(*args, **kwargs)
        
    def get_success_url(self):
        return reverse('frontpage')
    

class JoinRoom(View):
    def post(self, request, *args, **kwargs):
        room = Room.objects.get(pk=kwargs.get('room'))
        user = request.user
        member, created = Member.objects.get_or_create(room=room, user=user)
        """
        NOTE: When this is called from the room explorer, it can (?)
        cause a race condition it seems. Use lock in future (?)
        """

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
    

class RoomListView(ListView):
    model = Room
    template_name = 'rooms/explore-rooms.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(public=True)
        return queryset