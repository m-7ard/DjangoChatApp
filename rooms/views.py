from itertools import chain
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime, timezone

from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView, DeleteView, View, ListView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse 
from django.template.loader import render_to_string
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import requires_csrf_token
from django.utils.decorators import method_decorator

from users.models import CustomUser, Friend, Friendship
from .models import (
    GroupChat,
    GroupChatMembership,
    GroupChannel,
    Category,
    Invite,
    PrivateChat,
    PrivateChatMembership,
    BacklogGroupTracker,
    Emote,
    Emoji
)
from . import forms
from utils import get_object_or_none

channel_layer = get_channel_layer()

class DashboardView(TemplateView):
    template_name = 'rooms/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incoming_friendship_requests'] = self.request.user.received_friendships.pending().select_related('sender')
        context['accepted_friendship_requests'] = self.request.user.friendships().accepted().select_related('sender', 'receiver')
        context['outgoing_friendship_requests'] = self.request.user.sent_friendships.pending().select_related('receiver')
        return context
    

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['memberships'] = self.object.memberships.all().select_related('user')
        return context


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
        context['memberships'] = self.object.chat.memberships.all().select_related('user')
        return context


class CategoryCreateView(CreateView):
    form_class = forms.CategoryCreateForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Category',
            'fields': self.get_form(),
            'url': self.request.path,
            'type': 'create'
        }

        return context

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        category = form.save(commit=False)
        category.chat = GroupChat.objects.get(pk=self.kwargs.get('group_chat_pk'))
        category.save()

        return JsonResponse({'status': 400, 'redirect': self.request.META.get('HTTP_REFERER')})


class FriendshipFormView(FormView):
    form_class = forms.VerifyUser
    template_name = 'rooms/tooltips/add-friend.html'

    def form_valid(self, form):
        receiver = form.get_user()
        sender = self.request.user
        
        if receiver == sender:
            form.add_error(None, f'Cannot send friendship request to yourself.')
            return self.form_invalid(form)

        friendship = sender.friendships().intersection(receiver.friendships()).first()

        if friendship:
            status = friendship.status
            if status == 'pending':
                form.add_error(None, f'Already sent Friend Request to {receiver.full_name()}')
            elif status == 'accepted':
                form.add_error(None, f'Already Friends with {receiver.full_name()}')
                
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

        return JsonResponse({'status': 200, 'confirmation': f'Friend Request was sent to {receiver.full_name()}'})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})


class GroupChatInviteManageView(ListView):
    model = Invite
    template_name = 'rooms/overlays/manage-invites.html'
    context_object_name = 'invites'

    def get_queryset(self):
        group_chat = self.kwargs['group_chat_pk']
        return self.model.objects.filter(group_chat=group_chat)
    

class GetInviteView(TemplateView):
    template_name = 'rooms/overlays/get-invite.html'

    def get(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        kind = self.kwargs.get('kind')
        if kind == 'group_chat':
            group_chat = GroupChat.objects.get(pk=self.kwargs['pk'])
            context['invite'] = Invite.objects.create(kind='group_chat', group_chat=group_chat, created_by=self.request.user)
        
        return self.render_to_response(context)


class InviteCreateView(FormView):
    form_class = forms.InviteForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Invite',
            'fields': self.get_form(),
            'on_response': 'createInvite',
            'url': self.request.path,
            'type': 'create'
        }
        
        return context
    
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    
    def form_valid(self, form):
        invite = form.save(commit=False)
        kind = self.kwargs.get('kind')
        if kind == 'group_chat':
            invite.chat = GroupChat.objects.get(pk=self.kwargs['pk'])        
            invite.created_by = self.request.user

        invite.save()
        return JsonResponse({'status': 200, 'directory': invite.directory})


class InviteDeleteView(DeleteView):
    model = Invite

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    
    def form_valid(self, form):
        pk = self.object.pk
        self.object.delete()
        return JsonResponse({'status': 200, 'pk': pk})
        

class GroupChatLeaveView(TemplateView):
    template_name = 'rooms/overlays/leave-group-chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group_chat'] = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        return context
    

class PrivateChatDetailView(DetailView):
    model = PrivateChat
    template_name = 'rooms/private-chat.html'
    context_object_name = 'private_chat'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(*args, **kwargs)
        context['other_party'] = self.object.memberships.all().exclude(user=request.user).first()
        private_chat_membership = PrivateChatMembership.objects.get(user=request.user, chat=self.object)
        private_chat_membership.active = True
        private_chat_membership.save()

        return self.render_to_response(context)


class CreatePrivateChat(FormView):
    form_class = forms.VerifyUser
    template_name = 'rooms/overlays/create-private-chat.html'
    
    def form_valid(self, form):
        receiver = form.get_user()
        sender = self.request.user

        if receiver == sender:
            form.add_error(None, f'Cannot create private chat with yourself.')
            return self.form_invalid(form)

        private_chat = sender.private_chats().intersection(receiver.private_chats()).first()

        if private_chat:
            return JsonResponse({'status': 400, 'redirect': reverse('private-chat', kwargs={'pk': private_chat.pk})})
        else:
            private_chat = PrivateChat.objects.create()
            PrivateChatMembership.objects.create(user=sender, chat=private_chat, active=True)
            PrivateChatMembership.objects.create(user=receiver, chat=private_chat)
            # to track unread messages
            BacklogGroupTracker.objects.create(user=sender, backlog_group=private_chat.backlog_group)
            BacklogGroupTracker.objects.create(user=receiver, backlog_group=private_chat.backlog_group)
            return JsonResponse({'status': 200, 'redirect': reverse('private-chat', kwargs={'pk': private_chat.pk})})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})


class EmoteManageView(TemplateView):
    template_name = 'rooms/overlays/manage-emotes.html'
    form_class = forms.EmoteCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        context['group_chat'] = group_chat
        return context
     

class EmoteCreateView(CreateView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    model = Emote
    form_class = forms.EmoteCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Add Emote',
            'fields': self.form_class,
            'url': self.request.path,
            'on_response': 'addEmote',
            'type': 'create',
        }

        return context
    
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    
    def form_valid(self, form):
        emote = form.save(commit=False)
        emote.added_by = self.request.user
        emote.chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        emote.save()
        html = render_to_string('rooms/elements/emote-manager-item.html', {'emote': emote})
        return JsonResponse({'status': 200, 'html': html})


class EmoteUpdateView(UpdateView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    model = Emote
    form_class = forms.EmoteUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Edit Emote',
            'fields': self.get_form(),
            'url': self.request.path,
            'on_response': 'editEmote',
            'type': 'update',
        }

        return context
    
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    
    def form_valid(self, form):
        emote = form.save()
        return JsonResponse({'status': 200, 'pk': emote.pk, 'name': emote.name})


class EmoteDeleteView(DeleteView):
    model = Emote
    
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    
    def form_valid(self, form):
        pk = self.object.pk
        self.object.delete()
        return JsonResponse({'status': 200, 'pk': pk})


class EmoteMenuView(TemplateView):
    template_name = 'rooms/tooltips/emotes-menu.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_chat_pk = self.kwargs.get('group_chat_pk')
        context['group_chat'] = get_object_or_none(GroupChat, pk=group_chat_pk)
        categories = [
            'Smileys & Emotion', 
            'People & Body', 
            'Symbols', 
            'Objects'
            'Flags', 
            'Travel & Places', 
            'Food & Drink', 
            'Activities', 
            'Component', 
            'Animals & Nature', 
        ]
        context['emojis'] = {
            category: Emoji.objects.filter(category=category)
            for category in categories
        }
        return context
