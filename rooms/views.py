import os
import json
from itertools import chain
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime

from django import http
from django.db import models
from django.forms.models import BaseModelForm
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView, DeleteView, View, ListView
from django.shortcuts import HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse, JsonResponse 
from django.contrib import messages
from django.template.loader import render_to_string
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.mixins import UserPassesTestMixin

from users.models import CustomUser, Friend, Friendship
from core.models import News
from .models import (
    GroupChat,
    GroupChatMembership,
    GroupChannel,
    Category,
    Channel,
    Role,
    Invite
)
from . import forms
from utils import get_object_or_none

channel_layer = get_channel_layer()


class DashboardView(TemplateView):
    template_name = 'rooms/dashboard.html'


class GroupChatCreateView(CreateView):
    form_class = forms.GroupChatCreateForm
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
    context_object_name = 'group_chat'


class GroupChannelCreateView(CreateView):
    form_class = forms.GroupChannelCreateForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get(self, *args, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Channel',
            'fields': self.form_class,
            'url': self.request.path,
            'type': 'create'
        }

        return self.render_to_response(context)

    def form_invalid(self, form):
        return  JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        channel = form.save(commit=False)
        channel.chat = GroupChat.objects.get(pk=self.kwargs.get('group_chat_pk'))
        channel.category = Category.objects.filter(pk=self.kwargs.get('category_pk')).first()
        channel.save()

        success_url = reverse('group-channel', kwargs={'group_chat_pk': channel.chat.pk, 'group_channel_pk': channel.pk})  
        return JsonResponse({'status': 400, 'redirect': success_url})


class GroupChannelDetailView(DetailView):
    model = GroupChannel
    template_name = 'rooms/group-channel.html'
    context_object_name = 'group_channel'
    pk_url_kwarg = 'group_channel_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group_chat'] = self.object.chat
        return context


class CategoryCreateView(CreateView):
    form_class = forms.CategoryCreateForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get(self, *args, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Category',
            'fields': self.form_class,
            'url': self.request.path,
            'type': 'create'
        }

        return self.render_to_response(context)

    def form_invalid(self, form):
        return  JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        category = form.save(commit=False)
        category.chat = GroupChat.objects.get(pk=self.kwargs.get('group_chat_pk'))
        category.save()

        return JsonResponse({'status': 400, 'redirect': self.request.META.get('HTTP_REFERER')})


class FriendshipFormView(FormView):
    form_class = forms.FriendForm
    template_name = 'rooms/tooltips/add-friend.html'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        username_id = form.cleaned_data['username_id']
        full_username = f'{username}#{str(username_id).zfill(2)}'
        receiver = get_object_or_none(CustomUser, username=username, username_id=username_id)
        sender = self.request.user

        if not receiver:
            form.add_error(None, f'User {full_username} does not exist.')
            return self.form_invalid(form)
        
        if receiver == sender:
            form.add_error(None, f'Cannot send friendship request to yourself.')
            return self.form_invalid(form)

        friendship = sender.friendships().intersection(receiver.friendships()).first()

        if friendship:
            status = friendship.status
            if status == 'pending':
                form.add_error(None, f'Already sent Friend Request to {full_username}')
            elif status == 'accepted':
                form.add_error(None, f'Already Friends with {full_username}')
                
            return self.form_invalid(form)
        
        new_friendship = Friendship.objects.create(status='pending', sender=sender, receiver=receiver)
        sender_profile = Friend.objects.create(user=sender, friendship=new_friendship)
        receiver_profile = Friend.objects.create(user=receiver, friendship=new_friendship)

        async_to_sync(channel_layer.group_send)(
            f'user_{sender.pk}_dashboard', {
                'type': 'send_to_client',
                'action': 'create_friendship',
                'is_receiver': False,
                'html': render_to_string(template_name='rooms/elements/friend.html', context={'friend': receiver_profile, 'friendship': new_friendship})
            }
        )

        async_to_sync(channel_layer.group_send)(
            f'user_{receiver.pk}_dashboard', {
                'type': 'send_to_client',
                'action': 'create_friendship',
                'is_receiver': True,
                'html': render_to_string(template_name='rooms/elements/friend.html', context={'friend': sender_profile, 'friendship': new_friendship})
            }
        )

        async_to_sync(channel_layer.group_send)(
            f'user_{receiver.pk}', {
                'type': 'send_to_client',
                'action': 'create_notification',
                'id': 'dashboard-button',
            }
        )

        return JsonResponse({'status': 200, 'confirmation': f'Friend Request was sent to {full_username}'})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})


class InviteFormView(FormView):
    form_class = forms.InviteForm
    template_name = 'rooms/overlays/create-invite.html'

    def get(self, *args, **kwargs):
        group_chat = GroupChat.objects.get(pk=self.kwargs.get('group_chat_pk'))
        context = super().get_context_data(**kwargs)
        valid_invite = group_chat.invites.filter(expiry_date__gte=datetime.now()).exclude(one_time=True).first()
        context['invite'] = valid_invite if valid_invite else Invite.objects.create(chat=group_chat)
        return self.render_to_response(context)

    def form_valid(self, form):
        group_chat = GroupChat.objects.get(pk=self.kwargs.get('group_chat_pk'))
        invite = Invite.objects.create(chat=group_chat, expiry_date=form.cleaned_data['expiry_date'], one_time=form.cleaned_data['one_time'])
        return JsonResponse({'status': 200, 'invite_link': reverse('invite', kwargs={'directory': invite.directory})})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})


class InviteDetailView(DetailView):
    model = Invite
    template_name = 'rooms/invite.html'
    context_object_name = 'invite'

    def get_object(self):
        # Return None if there's no invite
        return Invite.objects.filter(directory=self.kwargs['directory']).first()
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.object:
            context['already_member'] = self.object.chat.memberships.all().filter(user=self.request.user).exists()
        
        return context
    
    def post(self, *args, **kwargs):
        invite = self.get_object()
        if invite and invite.is_valid():
            GroupChatMembership.objects.create(chat=invite.chat, user=self.request.user)
            if invite.one_time == True:
                invite.delete()

            return JsonResponse({'status': 200, 'redirect': reverse('group-chat', kwargs={'pk': invite.chat.pk})})
        else:
            return JsonResponse({'status': 400})
        
        
class GroupChatMembershipDeleteView(DeleteView):
    model = GroupChatMembership
    template_name = 'rooms/overlays/leave-group-chat.html'
    context_object_name = 'membership'
    success_url = reverse_lazy('dashboard')

    def get_object(self, queryset=None):
        group_chat_pk = self.kwargs.get('group_chat_pk')
        return GroupChatMembership.objects.get(Q(chat__pk=group_chat_pk) & Q(user=self.request.user))
    

"""

TODO: implement private chat, priority is sending invites over it rn
rework overlay, tooltip, form into one class(?)

"""




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