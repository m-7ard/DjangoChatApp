import os
import json
from itertools import chain
from typing import Any, Dict
from pathlib import Path

from django import http
from django.forms.models import BaseModelForm
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView, DeleteView, View, ListView
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse 
from django.contrib import messages
from django.template.loader import render_to_string
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from users.models import CustomUser
from core.models import News
from .models import (
    GroupChat,
    GroupChatMembership,
    Category,
    Channel,
    Role,
)
from .forms import (
    ChannelCreateForm,
    ChannelUpdateForm,

    ChannelDeleteForm,

    GroupChatCreateForm,
)


channel_layer = get_channel_layer()


class DashboardView(TemplateView):
    template_name = 'rooms/dashboard.html'


class CreateGroupChat(CreateView):
    form_class = GroupChatCreateForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get(self, *args, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Group Chat',
            'fields': self.form_class,
            'url': reverse('create-group-chat'),
            'type': 'create'
        }

        return self.render_to_response(context)

    def form_invalid(self, form):
        return  JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        group_chat = form.save(commit=False)
        group_chat.owner = self.request.user
        group_chat.save()

        success_url = reverse('group-chat', kwargs={'pk': group_chat.pk})

        async_to_sync(channel_layer.group_send)(f'user_{self.request.user.pk}', {
            'type': 'send_to_client',
            'action': 'create-group-chat',
            'html': render_to_string(request=self.request, template_name='core/elements/groupchat.html', context={'local_groupchat': group_chat})
        })

        return JsonResponse({'status': 400, 'redirect': success_url})
        

class GroupChatDetailView(DetailView):
    model = GroupChat
    template_name = 'rooms/group-chat.html'
    context_object_name = 'groupchat'

    
"""
class RoomView(DetailView):
    template_name = 'rooms/room.html'
    model = Room
    context_object_name = 'room'



class ChannelView(DetailView):
    template_name = 'rooms/channel.html'
    model = Channel
    context_object_name = 'channel'

    def get_object(self):
        return Channel.objects.get(pk=self.kwargs['channel'])

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        pass


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
            {
                'title': 'Manage Channel Permissions',
                'prerender': render_to_string(
                    request=request, 
                    template_name='rooms/forms/manage-channel-permissions.html', 
                    context= {
                        'title': 'Manage Channel Permissions',
                        'channel': channel,
                        'type': 'update'
                    }
                ),
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
        success_url = reverse('room', kwargs={'pk': self.object.room.pk})
        self.object.delete()
        return JsonResponse({'status': 400, 'redirect': success_url})
    

class RoomCreateView(CreateView):
    form_class = RoomCreateForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        context = self.get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Room',
            'fields': RoomCreateForm(),
            'url': reverse('create-room'),
            'type': 'create'
        }
        
        return render(request, self.template_name, context=context)
    
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        room = form.save(commit=False)
        room.owner = self.request.user
        room.save()
        success_url = reverse('room', kwargs={'pk': room.pk})
        return JsonResponse({'status': 400, 'redirect': success_url})
    

class RoomUpdateView(UpdateView):
    model = Room

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({'status': 400})


class LeaveRoom(TemplateView):
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['form'] = {
            'title': 'Leave Room',
            'fields': {},
            'url': reverse('leave-room', kwargs={'pk': kwargs.get('pk')}),
            'type': 'delete'
        }

        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        pass
    

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
        pass
    

class RoomListView(ListView):
    model = Room
    template_name = 'rooms/explore-rooms.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(public=True)
        return queryset
    

class ModelPermissionGroupUpdateView(View):
    pass
    


class PrivateChatView(TemplateView):
    template_name = 'rooms/private-chat.html'
    
    def get(self, request, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        counterparty = CustomUser.objects.get(pk=kwargs.get('pk'))
        private_chat = PrivateChat.objects.filter(
            Q(chatters__values__user=counterparty.pk) & Q(chatters__chatters__user=request.user.pk)
        ).first()

        if not private_chat:
            private_chat = PrivateChat.objects.create()
            Chatter.objects.create(user=request.user, group=private_chat.chatters)
            Chatter.objects.create(user=counterparty, group=private_chat.chatters)
        
        return self.render_to_response(context)
"""