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
from core.models import Archive
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
        context['accepted_friendship_requests'] = self.request.user.get_friendships().accepted().select_related('sender', 'receiver')
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
        memberships = self.object.memberships.all().select_related('user')
        context['memberships'] = memberships
        user_membership = memberships.get(user=self.request.user)
        context['context_member'] = user_membership
        context['visible_channels'] = user_membership.visible_channels()
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
        memberships = self.object.chat.memberships.all().select_related('user')
        context['memberships'] = memberships
        user_membership = memberships.get(user=self.request.user)
        context['context_member'] = user_membership
        context['visible_channels'] = user_membership.visible_channels()
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

        friendship = receiver.get_friendships().intersection(sender.get_friendships()).first()

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
                'html': render_to_string(template_name='rooms/elements/sidebar-users/friend.html', context={'friend': receiver_profile, 'friendship': new_friendship})
            }
        )

        async_to_sync(channel_layer.group_send)(
            f'user_{receiver.pk}_dashboard', {
                'type': 'send_to_client',
                'action': 'create_friendship',
                'is_receiver': True,
                'html': render_to_string(template_name='rooms/elements/sidebar-users/friend.html', context={'friend': sender_profile, 'friendship': new_friendship})
            }
        )

        async_to_sync(channel_layer.group_send)(
            f'user_{receiver.pk}', {
                'type': 'send_to_client',
                'action': 'create_notification',
                'id': 'dashboard-button',
                'modifier': 'dashboard'
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

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        kind = self.kwargs.get('kind')

        if kind == 'group_chat':
            group_chat = GroupChat.objects.get(pk=self.kwargs['pk'])
            membership = group_chat.memberships.get(user=self.request.user)
            context['context_member'] = membership
            if membership.has_perm('can_create_invites'):
                context['invite'] = Invite.objects.create(kind='group_chat', group_chat=group_chat, user=self.request.user)
            elif membership.has_perm('can_get_invites'):
                context['invite'] = group_chat.invites.filter(expiry_date__gt=datetime.now(timezone.utc)).first()

        return context
    

class InviteCreateView(CreateView):
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
        invite.kind = kind

        if kind == 'group_chat':
            invite.group_chat = GroupChat.objects.get(pk=self.kwargs['pk'])        
            invite.user_archive = self.request.user.archive_wrapper
        
        invite.save()
        return JsonResponse({'status': 200, 'directory': invite.full_link()})


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
        private_chat = self.object
        context = super().get_context_data(*args, **kwargs)
        private_chat_membership = PrivateChatMembership.objects.get(user_archive__user=request.user, chat=private_chat)
        context['other_party'] = private_chat_membership.other_party()
        private_chat_membership.active = True
        private_chat_membership.save()

        return self.render_to_response(context)


class EmoteManageView(TemplateView):
    template_name = 'rooms/overlays/manage-emotes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        context['group_chat'] = group_chat
        return context
     

class EmoteCreateView(CreateView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    form_class = forms.EmoteCreateForm
    model = Emote

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
        group_chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        group_chat_membership = group_chat.memberships.get(user=self.request.user)

        if not group_chat_membership.has_perm('can_manage_emotes'):
            form.add_error(None, f'User lacks permission to manage emotes.')
            return self.form_invalid(form)

        if emote.name in group_chat.emotes.values_list('name', flat=True):
            form.add_error('name', f'Emote with name "{emote.name}" already exists.')
            return self.form_invalid(form)
        
        emote.user_archive = self.request.user.archive_wrapper
        emote.chat = group_chat
        emote.save()
        html = render_to_string('rooms/elements/manager-items/emote-manager-item.html', {'emote': emote})
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
        group_chat = emote.chat
        group_chat_membership = group_chat.memberships.get(user=self.request.user)

        if not group_chat_membership.has_perm('can_manage_emotes'):
            form.add_error(None, f'User lacks permission to manage emotes.')
            return self.form_invalid(form)

        if emote.name in group_chat.emotes.values_list('name', flat=True):
            form.add_error('name', f'Emote with name "{emote.name}" already exists.')
            return self.form_invalid(form)

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
            'Objects',
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
            archive = get_object_or_none(Archive, data__pk=kwargs.get('user_pk'), data__model='CustomUser')
            if not archive:
                return None
            
            return render(request, 'commons/tooltips/archived-user-profile-card.html', {'archive': archive})
        
        backlog_group = get_object_or_none(BacklogGroup, pk=kwargs.get('backlog_group_pk'))
        if backlog_group and backlog_group.kind == 'group_channel':
            group_chat = backlog_group.get_chat()
            member = group_chat.get_member(user=user)
            return render(request, 'commons/tooltips/group-chat-member-profile-card.html', {'member': member})
            
        return render(request, 'commons/tooltips/user-profile-card.html', {'profile_user': user})


class PrivateChatGetOrCreateView(FormView):
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
        return JsonResponse({'status': 400})

    def form_valid(self, form):
        other_party = form.get_user()
        if self.request.user == other_party:
            return self.form_invalid(form)
        
        existing_private_chat = self.request.user.get_private_chats().intersection(other_party.get_private_chats()).first()
        
        if existing_private_chat:
            return JsonResponse({'status': 200, 'redirect': reverse('private-chat', kwargs={'pk': existing_private_chat.pk})})

        new_private_chat = PrivateChat.objects.create()
        PrivateChatMembership.objects.create(chat=new_private_chat, user=other_party)
        PrivateChatMembership.objects.create(chat=new_private_chat, user=self.request.user)
        return JsonResponse({'status': 200, 'redirect': reverse('private-chat', kwargs={'pk': new_private_chat.pk})})


class RoleManageView(TemplateView):
    template_name = 'rooms/overlays/manage-roles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group_chat'] = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        return context


class RoleDeleteView(DeleteView):
    model = Role

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    
    def form_valid(self, form):
        role = self.object
        pk = role.pk
        group_chat = role.chat
        group_chat_membership = group_chat.memberships.get(user=self.request.user)
        
        if not group_chat_membership.has_perm('can_manage_roles'):
            form.add_error(None, f'User lacks permission to manage roles.')
            return self.form_invalid(form)
        
        role.delete()
        return JsonResponse({'status': 200, 'pk': pk, 'handler': 'deleteRole'})
    

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
            'type': 'create',
        }
        return context
    
    def form_valid(self, form):
        role = form.save(commit=False)
        group_chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        group_chat_membership = group_chat.memberships.get(user=self.request.user)
        
        if not group_chat_membership.has_perm('can_manage_roles'):
            form.add_error(None, f'User lacks permission to manage roles.')
            return self.form_invalid(form)

        if role.name in group_chat.roles.values_list('name', flat=True):
            form.add_error('name', f'Role with name "{role.name}" already exists.')
            return self.form_invalid(form)

        role.chat = GroupChat.objects.get(pk=self.kwargs['group_chat_pk'])
        role.save()
        form.save_m2m()

        return JsonResponse({'status': 200, 'handler': 'createRole', 'html': render_to_string('rooms/elements/manager-items/role-manager-item.html', {'role': role})})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    

class RoleUpdateView(UpdateView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    model = Role

    def get_form(self, form_class=None):
        group_chat = self.object.chat

        if self.object == group_chat.base_role:
            form = super().get_form(form_class=forms.BaseRoleUpdateForm)
        else:
            form = super().get_form(form_class=forms.RoleUpdateForm)
        
        form.fields['can_see_channels'].queryset = group_chat.channels.all()
        form.fields['can_see_channels'].widget.attrs['choices'] = ((channel.pk, channel.name) for channel in group_chat.channels.all())
        form.fields['can_see_channels'].widget.attrs['initial'] = self.object.can_see_channels.values_list('pk', flat=True)

        form.fields['can_use_channels'].queryset = group_chat.channels.all()
        form.fields['can_use_channels'].widget.attrs['choices'] = ((channel.pk, channel.name) for channel in group_chat.channels.all())
        form.fields['can_use_channels'].widget.attrs['initial'] = self.object.can_use_channels.values_list('pk', flat=True)
        
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Edit Role',
            'fields': self.get_form(),
            'url': self.request.path,
            'type': 'update',
        }
        return context
    
    def form_valid(self, form):
        role = form.save(commit=False)
        group_chat = role.chat
        group_chat_membership = group_chat.memberships.get(user=self.request.user)
                
        if not group_chat_membership.has_perm('can_manage_roles'):
            form.add_error(None, f'User lacks permission to manage roles.')
            return self.form_invalid(form)

        role.save()
        form.save_m2m()

        return JsonResponse({'status': 200, 'handler': 'editRole', 'pk': role.pk, 'html': render_to_string('rooms/elements/manager-items/role-manager-item.html', {'role': role})})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    

class RoleManageMembersView(UpdateView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    form_class = forms.RoleManageMembersForm
    model = Role

    def get(self, request, *args, **kwargs):
        role = self.get_object()
        if role == role.chat.base_role:
            return render(request, 'commons/overlays/error.html', context={'message': 'Cannot edit base role members'})

        return super().get(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class=self.form_class)
        group_chat = self.object.chat
        memberships = group_chat.memberships.all().select_related('user')
        
        form.fields['members'].queryset = memberships
        form.fields['members'].widget.attrs['choices'] = ((member.pk, member.user.full_name()) for member in memberships.order_by('user__username', 'user__username_id'))
        form.fields['members'].widget.attrs['initial'] = self.object.members.values_list('pk', flat=True)

        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Manage Role Members',
            'fields': self.get_form(),
            'url': self.request.path,
            'type': 'update',
        }
        return context
    
    def form_valid(self, form):
        role = form.save()

        return JsonResponse({'status': 200, 'handler': 'editRoleMemberCount', 'pk': role.pk, 'count': role.members.count()})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    

class RoleOrderUpdateView(UpdateView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    form_class = forms.RoleOrderUpdateForm
    pk_url_kwarg = 'group_chat_pk'
    model = GroupChat

    def get_form(self, form_class=None):
        form = super().get_form(form_class=self.form_class)
        group_chat = self.object
        base_role = group_chat.base_role
        roles = sorted(group_chat.roles.exclude(pk=base_role.pk), key=lambda role: role.get_order())
        form.fields['role_order'].widget.value = roles
        form.fields['role_order'].widget.attrs['choices'] = ((role.pk, role.name) for role in roles)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Update Role Order',
            'fields': self.get_form(),
            'url': self.request.path,
            'type': 'update',
        }
        return context
    
    def form_valid(self, form):
        form.save()
        return JsonResponse({'status': 200, 'confirmation': 'Successfully update role order'})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    