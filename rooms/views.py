from itertools import chain
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime, timezone
from django.forms.models import BaseModelForm

from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, FormView, DeleteView, View, ListView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, JsonResponse 
from django.template.loader import render_to_string
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import requires_csrf_token
from django.utils.decorators import method_decorator
from django.shortcuts import render

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
    Emoji,
    BacklogGroup,
    Role,
)
from . import forms
from utils import get_object_or_none, process_mention

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Group Chat',
            'fields': self.get_form(),
            'url': self.request.path,
            'type': 'create'
        }

        return context

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    def form_valid(self, form):
        group_chat = form.save(commit=False)
        group_chat.owner = self.request.user
        group_chat.save()

        async_to_sync(channel_layer.group_send)(f'user_{self.request.user.pk}', {
            'type': 'send_to_client',
            'action': 'create_group_chat',
            'html': render_to_string(request=self.request, template_name='core/elements/group-chat.html', context={'local_group_chat': group_chat})
        })

        return JsonResponse({'status': 200, 'redirect': reverse('group-chat', kwargs={'pk': group_chat.pk})})
        

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
        group_chat = GroupChat.objects.get(pk=self.kwargs.get('group_chat_pk'))
        channel.chat = group_chat
        channel.category = Category.objects.filter(pk=self.kwargs.get('category_pk')).first()
        channel.save()

        async_to_sync(channel_layer.group_send)(f'group_chat_{group_chat.pk}', {
            'type': 'send_to_client',
            'action': 'create_group_channel',
            'html': render_to_string(request=self.request, template_name='rooms/elements/channel.html', context={'channel': channel}),
            'category': getattr(channel, 'category', None) and channel.category.pk,
        })

        return JsonResponse({'status': 400, 'redirect': reverse('group-channel', kwargs={'group_chat_pk': channel.chat.pk, 'group_channel_pk': channel.pk})  })


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
        group_chat = GroupChat.objects.get(pk=self.kwargs.get('group_chat_pk'))
        category.chat = group_chat
        category.save()

        async_to_sync(channel_layer.group_send)(f'group_chat_{group_chat.pk}', {
            'type': 'send_to_client',
            'action': 'create_group_category',
            'html': render_to_string(request=self.request, template_name='rooms/elements/category.html', context={'category': category}),
        })

        return JsonResponse({'status': 400, 'redirect': self.request.META.get('HTTP_REFERER')})


class FriendshipFormView(FormView):
    form_class = forms.VerifyUser
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Add Friend',
            'fields': self.get_form(),
            'url': self.request.path,
            'type': 'create'
        }

        return context

    def form_valid(self, form):
        receiver = form.get_user()
        sender = self.request.user
        
        if receiver == sender:
            form.add_error('user', f'Cannot send friendship request to yourself.')
            return self.form_invalid(form)

        friendship = Friendship.objects.filter(Q(members__user=sender) & Q(members__user=receiver)).first()

        if friendship:
            status = friendship.status
            if status == 'pending':
                form.add_error('user', f'Already sent Friend Request to {receiver.full_name()}')
            elif status == 'accepted':
                form.add_error('user', f'Already Friends with {receiver.full_name()}')
                
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


class PrivateChatFormView(FormView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    form_class = forms.VerifyUser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Private Chat',
            'fields': self.get_form(),
            'url': self.request.path,
            'type': 'create'
        }

        return context
    
    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    
    def form_valid(self, form):
        other_party = form.get_user()
        existing_private_chat = PrivateChat.objects.filter(memberships__user=other_party).filter(memberships__user=self.request.user).first()

        if existing_private_chat:
            return JsonResponse({'status': 200, 'redirect': reverse('private-chat', kwargs={'pk': existing_private_chat.pk})})
        else:
            new_private_chat = PrivateChat.objects.create()
            PrivateChatMembership.objects.create(chat=new_private_chat, user=other_party)
            PrivateChatMembership.objects.create(chat=new_private_chat, user=self.request.user)
            return JsonResponse({'status': 200, 'redirect': reverse('private-chat', kwargs={'pk': new_private_chat.pk})})


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


class UserProfileCardView(View):
    def get(self, request, *args, **kwargs):
        user = get_object_or_none(CustomUser, pk=kwargs.get('user_pk'))
        
        if not user:
            return
        
        if kwargs.get('backlog_group_pk'):
            backlog_group = get_object_or_none(BacklogGroup, pk=kwargs.get('backlog_group_pk'))
            if backlog_group:
                return self.get_profile_from_backlog_group(request, backlog_group, user)
        
        if kwargs.get('group_chat_pk'):
            group_chat = get_object_or_none(GroupChat, pk=kwargs.get('group_chat_pk'))
            membership = group_chat.memberships.filter(user=user).first()
            if group_chat and membership:
                return render(request, 'rooms/tooltips/group-chat-member-profile-card.html', {'membership': membership})

        return render(request, 'commons/tooltips/user-profile-card.html', {'profile_user': user})

    def get_profile_from_backlog_group(self, request, backlog_group, user):
        if backlog_group.kind == 'group_channel':
            membership = get_object_or_none(GroupChatMembership, user=user, chat=backlog_group.group_channel.chat)
            if membership:
                return render(request, 'rooms/tooltips/group-chat-member-profile-card.html', {'membership': membership})

        
class GetOrCreatePrivateChat(FormView):
    form_class = forms.VerifyUser

    def form_invalid(self, form):
        return JsonResponse({'status': 400})

    def form_valid(self, form):
        other_party = form.get_user()
        if self.request.user == other_party:
            return self.form_invalid(form)
        
        existing_private_chat = self.request.user.private_chats().intersection(other_party.private_chats()).first()
        if existing_private_chat:
            return JsonResponse({'status': 200, 'redirect': reverse('private-chat', kwargs={'pk': existing_private_chat.pk})})
        else:
            new_private_chat = PrivateChat.objects.create()
            PrivateChatMembership.objects.create(chat=new_private_chat, user=other_party)
            PrivateChatMembership.objects.create(chat=new_private_chat, user=self.request.user)
            return JsonResponse({'status': 200, 'redirect': reverse('private-chat', kwargs={'pk': new_private_chat.pk})})
        
    
class GetMentionablesView(TemplateView):
    template_name = 'rooms/tooltips/mentionables-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backlog_group = BacklogGroup.objects.get(pk=self.kwargs['backlog_group_pk'])
        alphanumeric, numeric = process_mention(self.kwargs['mention'])
        if backlog_group.kind == 'group_channel':
            chat = backlog_group.group_channel.chat
            context['members'] = chat.memberships.filter(
                Q(nickname__icontains=alphanumeric)
                | Q(user__username__icontains=alphanumeric)
            )[:10] if alphanumeric else chat.memberships.all()[:10]
            if numeric:
                context['members'] = filter(lambda member: numeric in member.user.formatted_username_id(), context['members'])
            context['roles'] = chat.roles.filter(name__icontains=alphanumeric) if alphanumeric else chat.roles.all()[:10]
        elif backlog_group.kind == 'private_chat':
            chat = backlog_group.private_chat
            context['members'] = chat.memberships.filter(
                Q(nickname__icontains=alphanumeric)
                | Q(user__username__icontains=alphanumeric)
            )[:10] if alphanumeric else chat.memberships.all()[:10]
        
        return context


class RoleManageView(TemplateView):
    template_name = 'rooms/overlays/manage-roles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group_chat'] = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        return context


class RoleDeleteView(DeleteView):
    model = Role


class RoleCreateView(CreateView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    form_class = forms.RoleCreateForm
    model = Role

    def get_form(self, form_class=None):
        form = super().get_form(form_class=self.form_class)
        group_chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        
        form.fields['can_see_channels'].queryset = group_chat.channels.all()
        form.fields['can_see_channels'].widget.attrs['choices'] = ((channel.pk, channel.name) for channel in group_chat.channels.all())
        form.fields['can_see_channels'].widget.attrs['initial'] = group_chat.channels.values_list('pk', flat=True)

        form.fields['can_use_channels'].queryset = group_chat.channels.all()
        form.fields['can_use_channels'].widget.attrs['choices'] = ((channel.pk, channel.name) for channel in group_chat.channels.all())
        form.fields['can_use_channels'].widget.attrs['initial'] = group_chat.channels.values_list('pk', flat=True)
        
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Create Role',
            'fields': self.get_form(),
            'url': self.request.path,
            'on_response': 'createRole',
            'type': 'create',
        }
        return context

    def post(self, request, *args, **kwargs):
        pass
    
    def form_valid(self, form):
        role = form.save(commit=False)
        role.chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        form.save()

        return JsonResponse({'status': 200, 'handler': 'createRole'})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})

    """
    finish role create view
    implement permission checking
    
    
    """