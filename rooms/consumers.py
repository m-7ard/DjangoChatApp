import json
import datetime
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Q

from .models import (
    Backlog,
    GroupChat,
    GroupChannel,
    Message,
    PrivateChat,
    BacklogGroupTracker,
    PrivateChatMembership,
    Emoji,
    Emote,
    Reaction,
    Invite,
    GroupChatMembership,
    Log,

)
from users.models import Friend
from utils import get_object_or_none, base64_file
from DjangoChatApp.templatetags.custom_tags import get_member_or_none

@sync_to_async
def process_mention(mention):
    import re

    alphanumeric_pattern = r'>>([a-zA-Z0-9]+)'
    numeric_pattern = r'#(\d{1,2})?$'
    
    alphanumeric_match = re.search(alphanumeric_pattern, mention)
    numeric_match = re.search(numeric_pattern, mention)
    
    alphanumeric = alphanumeric_match.group(1) if alphanumeric_match else None
    numeric = numeric_match.group(1) if numeric_match else None
    
    return alphanumeric, numeric


@database_sync_to_async
def get_foreign_keys(name, *objects):
    return [getattr(object_, name) for object_ in objects]

@database_sync_to_async
def get_foreign_key(name, object_):
    return getattr(object_, name)

@database_sync_to_async
def db_async(fn):
    return fn()


class AppConsumer(AsyncWebsocketConsumer):
    async def connect(self, chat=None):
        self.user = self.scope.get('user')
        self.user_archive = await get_foreign_key('archive_wrapper', self.user)

        if not self.user or not self.user.is_authenticated:
            return self.close()
        
        self.csrf_token = self.scope['cookies']['csrftoken']
        self.loop = asyncio.get_event_loop()
        await self.channel_layer.group_add(f'user_{self.user.pk}', self.channel_name)
        await self.create_extra_path()
        await self.connect_user_to_chats()
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        print('received: ', data)
        handler = getattr(self, data['action'])
        await handler(**data)
    
    async def disconnect(self, close_code):
        await self.close()

    async def create_extra_path(self):
        extra_path = self.scope['url_route']['kwargs'].get('extra_path')
        self.extra_path = extra_path.split('/') if extra_path else []

        if 'self' in self.extra_path:
            await self.channel_layer.group_add(f'user_{self.user.pk}_self', self.channel_name)
        if 'dashboard' in self.extra_path:
            await self.channel_layer.group_add(f'user_{self.user.pk}_dashboard', self.channel_name)

    async def send_to_client(self, event):
        print('sending', 'data: ', event)
        await self.send(text_data=json.dumps(event))

    async def create_new_backlog_notification(self, event):
        @database_sync_to_async
        def allow_notification(sender: int, target_backlog_group: int, backlog: int, **kwargs):
            # backlog was sent by the same user
            is_sender = (sender == self.user.pk)
            if is_sender:
                return False, 'is sender'
            
            # the user already saw the message
            target_backlog_group_tracker = BacklogGroupTracker.objects.get(user=self.user, backlog_group=target_backlog_group)
            last_backlog = target_backlog_group_tracker.last_backlog_seen
            last_backlog_pk = last_backlog.pk if last_backlog else None
            already_seen_backlog = last_backlog_pk and (last_backlog_pk >= backlog)
            if already_seen_backlog:
                return False, 'already saw backlog'

            return True, 'ok to send'
        
        async def delegate_notification_creation(notification_type: str, target_backlog_group: int, **kwargs):
            await asyncio.sleep(2)
            # print reason for debug purposes
            send_notification, reason = await allow_notification(**event)
            if not send_notification:
                return
            
            if notification_type == 'private_chat_notification':
                channels_sends = await self.create_private_chat_notification(backlog_group=target_backlog_group, private_chat=kwargs['private_chat'])
                for send in channels_sends:
                    await send
            elif notification_type == 'group_chat_notification':
                channels_sends = await self.create_group_chat_notification(group_chat=kwargs['group_chat'], group_channel=kwargs['group_channel'])
                for send in channels_sends:
                    await send

        self.loop.create_task(delegate_notification_creation(**event))
        
    @sync_to_async
    def create_private_chat_notification(self, backlog_group, private_chat):
        receiver = PrivateChatMembership.objects.get(chat__pk=private_chat, user=self.user)
        # The private chat will now appear on the clients /self/... left side sidebar
        channels_sends = []
        
        if 'self' in self.extra_path:
            channels_sends.append(self.send_to_client({
                'action': 'create_notification',
                'id': f'private-chat-{private_chat}',
                'modifier': 'private-chat'
            }))

        channels_sends.append(self.send_to_client({
            'action': 'create_notification',
            'id': f'dashboard-button',
            'modifier': 'dashboard'
        }))

        return channels_sends
    
    @sync_to_async
    def create_group_chat_notification(self, group_chat, group_channel):
        channels_sends = []

        if hasattr(self, 'group_chat'):
            channels_sends.append(self.send_to_client({
                'action': 'create_notification',
                'id': f'group-channel-{group_channel}',
                'modifier': 'hidden'
            }))

        channels_sends.append(self.send_to_client({
            'action': 'create_notification',
            'id': f'group-chat-{group_chat}',
            'modifier': 'hidden'
        }))

        return channels_sends

    async def connect_user_to_chats(self):
        """ 
            This method makes the user listen to all backlogs groups they're in.
        """
        # using list(...) due to queryset not being iterable in async context
        user_backlog_groups = await db_async(
            lambda: list(self.user.backlog_trackers.values_list('backlog_group', flat=True))
        )
        for backlog_group in user_backlog_groups:
            await self.channel_layer.group_add(f'backlog_group_{backlog_group}', self.channel_name)
    
    async def accept_friendship(self, pk, **kwargs):
        @database_sync_to_async
        def accept_friendship():
            friend = Friend.objects.get(pk=pk)
            friendship = friend.friendship
            friendship.status = 'accepted'
            friendship.save()

            sender_profile = friendship.sender_profile()
            receiver_profile = friendship.receiver_profile()

            return sender_profile, receiver_profile
        
        sender_profile, receiver_profile = await accept_friendship()
        sender_user, receiver_user = await get_foreign_keys('user', sender_profile, receiver_profile)
        
        await self.channel_layer.group_send(
            f'user_{sender_user.pk}_dashboard', {
                'type': 'send_to_client',
                'pk': receiver_profile.pk,
                'is_receiver': False,
                **kwargs
            }
        )

        await self.channel_layer.group_send(
            f'user_{receiver_user.pk}_dashboard', {
                'type': 'send_to_client',
                'pk': sender_profile.pk,
                'is_receiver': True,
                **kwargs
            }
        )

        await self.channel_layer.group_send(
            f'user_{receiver_user.pk}', {
                'type': 'send_to_client',
                'action': 'remove_notification',
                'id': 'dashboard-button',
            }
        )

    async def delete_friendship(self, pk, **kwargs):
        @database_sync_to_async
        def delete_friendship():
            friend = Friend.objects.get(pk=pk)
            friendship = friend.friendship
            cancelled = True if friendship.status == 'pending' else False

            sender_profile = friendship.sender_profile()
            receiver_profile = friendship.receiver_profile()

            friendship.delete()

            return cancelled, sender_profile, receiver_profile
        
        cancelled, sender_profile, receiver_profile = await delete_friendship()
        sender_user, receiver_user = await get_foreign_keys('user', sender_profile, receiver_profile)

        await self.channel_layer.group_send(
            f'user_{sender_user.pk}_dashboard', {
                'type': 'send_to_client',
                'action': 'delete_friendship',
                'pk': receiver_profile.pk,
            }
        )

        await self.channel_layer.group_send(
            f'user_{receiver_user.pk}_dashboard', {
                'type': 'send_to_client',
                'action': 'delete_friendship',
                'pk': sender_profile.pk,
            }
        )

        if cancelled:
            await self.channel_layer.group_send(
                f'user_{receiver_user.pk}', {
                    'type': 'send_to_client',
                    'action': 'remove_notification',
                    'id': 'dashboard-button',
                }
            )


    @sync_to_async
    def join_group_chat(self, invite):
        group_chat = invite.group_chat
        GroupChatMembership.objects.create(user=self.user, chat=group_chat)
        channel = group_chat.channels.first()
        backlog = Backlog.objects.create(kind='log', group=channel.backlog_group)
        log = Log.objects.create(backlog=backlog, action='join', user1=self.user)
        if invite.one_time:
            invite.delete()

        return [
            self.channel_layer.group_send(
                f'group_chat_{group_chat.pk}', {
                    'type': 'send_log_to_client',
                    'action': 'create_log',
                    'pk': backlog.pk,
                }
            ),
            self.channel_layer.group_send(
                f'user_{self.user.pk}', {
                    'type': 'send_to_client',
                    'action': 'join_group_chat',
                    'html': render_to_string('core/elements/group-chat.html', context={'local_group_chat': group_chat, 'user': self.user}),
                }
            ),
            self.send(text_data=json.dumps({
                'action': 'redirect',
                'url': reverse('group-channel', kwargs={'group_chat_pk': group_chat.pk, 'group_channel_pk': channel.pk})
            })),
        ]

    async def accept_invite(self, directory, **kwargs):
        invite = await db_async(lambda: Invite.objects.get(directory=directory))
        if invite.kind == 'group_chat':
            group_sends = await self.join_group_chat(invite)

        for group_send in group_sends:
            await group_send


class BacklogGroupUtils():
    @sync_to_async
    def mark_as_read(self):
        new_backlogs = self.tracker.unread_backlogs()
        new_backlogs_count = new_backlogs.count()

        if new_backlogs_count:
            self.tracker.last_backlog_seen = self.backlog_group.backlogs.last()
            self.tracker.save()
            # messages of the very same user do not (and should not)
            # produce notifications
            return new_backlogs.exclude(message__user_archive=self.user_archive).count()

        return 0
    
    @sync_to_async
    def is_mentioned(self, pk):
        backlog = Backlog.objects.get(pk=pk)
        user_mentioned = self.user in backlog.user_mentions.all() 
        if user_mentioned:
            return True

        chat = self.get_chat()
        member = chat.memberships.filter(user=self.user).first()
        mentioned = member.roles.all().intersection(backlog.role_mentions.all()).exists()
        
        return mentioned
    
    async def send_log_to_client(self, event):
        await self.send(text_data=json.dumps({
            'action': event['action'],
            'html': await self.render_backlog(event['pk']),
        }))
    
    async def send_message_to_client(self, event):
        await self.send(text_data=json.dumps({
            'action': event['action'],
            'is_sender': (event['sender'] == self.user.pk),
            'html': await self.render_backlog(event['pk']),
        }))

    async def update_message_to_client(self, event):
        await self.send(text_data=json.dumps({
            'action': event['action'],
            'pk': event['pk'],
            'content': event['content'],
            'is_mentioned': await self.is_mentioned(event['pk']),
            'invites': await self.render_invites(*event['invites']),
        }))

    @sync_to_async
    def delete_backlog(self, pk):
        backlog = get_object_or_none(Backlog, pk=pk)
        if not backlog or backlog.group != self.backlog_group:
            return False
        
        member = get_member_or_none(self.user, self.get_chat())
        if backlog.kind == 'log':
            can_delete = member.has_perm('can_manage_backlogs')   
        elif backlog.kind == 'message':
            can_delete = (self.user_archive == backlog.message.user_archive) or  member.has_perm('can_manage_backlogs')

        if can_delete:
            backlog.delete()
            return True

    @sync_to_async
    def create_message(self, content=None, file=None):
        if file:
            file = base64_file(file['data'], file['name'])
        
        backlog = Backlog.objects.create(kind='message', group=self.backlog_group)
        message = Message.objects.create(user_archive=self.user_archive, content=content, backlog=backlog, attachment=file)
        
        return backlog
    
    @sync_to_async
    def render_backlog(self, pk):
        backlog = Backlog.objects.get(pk=pk)
        if backlog.kind == 'message':
            return render_to_string('rooms/elements/message.html', {'backlog': backlog, 'user': self.user, 'chat': self.get_chat()})
        elif backlog.kind == 'log':
            return render_to_string('rooms/elements/log.html', {'backlog': backlog, 'user': self.user})

    @sync_to_async
    def render_invites(self, *invites):
        rendered_invites = []
        for invite in invites:
            if not invite['valid']:
                rendered_invites.append(render_to_string('rooms/elements/backlog-invites/invalid-backlog-invite.html'))
            elif invite['is_expired']:
                rendered_invites.append(render_to_string('rooms/elements/backlog-invites/expired-backlog-invite.html'))
            else:
                rendered_invites.append(render_to_string('rooms/elements/backlog-invites/valid-backlog-invite.html', {'invite': invite, 'user': self.user}))
            
        return ''.join(rendered_invites)

    @sync_to_async
    def edit_message(self, pk, content):
        backlog = get_object_or_none(Backlog, pk=pk)
        
        if (
            not backlog 
            or backlog.group != self.backlog_group
            or backlog.message.user != self.user
        ):
            return

        message = backlog.message
        message.content = content
        message.save()
        send_data = {
            'type': 'update_message_to_client',
            'action': 'edit_message',
            'content': message.rendered_content,
            'invites': backlog.message.process_invites(),
            'pk': pk,
        }

        return send_data
    
    @sync_to_async
    def create_common_attributes(self, chat):
        self.backlog_group = chat.backlog_group
        self.tracker = BacklogGroupTracker.objects.get(user=self.user, backlog_group=self.backlog_group)
        backlogs = self.backlog_group.backlogs.select_related('message__user_archive', 'log__user1_archive', 'log__user2_archive').order_by('-pk')
        self.paginator = Paginator(backlogs, 20)
        self.current_page = self.paginator.get_page(1)

    async def generate_backlogs(self, **kwargs):
        if self.current_page == None:
            return
        
        backlogs = self.current_page.object_list
        html = await sync_to_async(render_to_string)(
            template_name='rooms/elements/backlogs.html',
            context={
                'backlogs': backlogs, 
                'user': self.user, 
                'chat': await sync_to_async(self.get_chat)()
            },
        )
        await self.send(json.dumps({
            'type': 'send_to_client',
            'action': 'generate_backlogs',
            'html': html,
            'page': self.current_page.number,
        }))

        await self.prepare_next_page()

    @sync_to_async
    def prepare_next_page(self):
        if self.current_page.has_next():
            next_page_number = self.current_page.next_page_number()
            self.current_page = self.paginator.get_page(next_page_number)
        else:
            self.current_page = None
        
    @sync_to_async
    def get_mentionables(self, chat, alphanumeric, numeric, kind):
        context = {}

        if kind == 'group_chat':
            context['members'] = chat.memberships.filter(
                Q(nickname__icontains=alphanumeric)
                | Q(user__username__icontains=alphanumeric)
            )[:10] if alphanumeric else chat.memberships.all()[:10]
            if numeric:
                context['members'] = filter(lambda member: numeric in member.user.formatted_username_id(), context['members'])
            context['roles'] = chat.roles.filter(name__icontains=alphanumeric) if alphanumeric else chat.roles.all()[:10]
        elif kind == 'private_chat':
            context['members'] = chat.memberships.filter(
                user__username__icontains=alphanumeric
            )[:10] if alphanumeric else chat.memberships.all()[:10]

        html = render_to_string(template_name='rooms/tooltips/mentionables-list.html', context=context)

        return html
    
    @sync_to_async
    def emote_reaction(self, backlog_pk, emote_pk):
        emote = Emote.objects.get(pk=emote_pk)
        backlog = Backlog.objects.get(pk=backlog_pk)
        if not emote or not backlog:
            return
        
        action = self.process_reaction(reaction_kwargs={'emote': emote, 'backlog': backlog, 'kind': 'emote'})
        send_data = {
            'action': action,
            'emoticon_pk': emote_pk,
            'backlog_pk': backlog_pk,
        }
        if action == 'create_reaction':
            send_data['image'] = str(emote.image)

        return send_data

    @sync_to_async
    def validate_react_backlog_input(self, kind, emoticon_pk, backlog_pk):
        backlog = get_object_or_none(Backlog, pk=backlog_pk)
        if not backlog or backlog not in self.backlog_group.backlogs.all():
            return False
    
        # TODO: check if user has permission to add reactions
        
        if kind == 'emoji':
            emoticon = get_object_or_none(Emoji, pk=emoticon_pk)
            if not emoticon:
                return False
        elif kind == 'emote':
            if not hasattr(self, 'group_chat'):
                return False
            
            emoticon = self.group_chat.emotes.filter(pk=emoticon_pk).first()
            if not emoticon:
                return False
        
        return True

    @sync_to_async
    def process_reaction(self, kind, emoticon_pk, backlog_pk):
        backlog = Backlog.objects.get(pk=backlog_pk)
    
        if kind == 'emoji':
            emoticon = Emoji.objects.get(pk=emoticon_pk)
            reaction, created = Reaction.objects.get_or_create(kind=kind, backlog=backlog, emoji=emoticon)
        elif kind == 'emote':
            emoticon = Emote.objects.get(pk=emoticon_pk)
            reaction, created = Reaction.objects.get_or_create(kind=kind, backlog=backlog, emote=emoticon)

        if created:
            reaction.users.add(self.user)
            action = 'create_reaction' if reaction.users.count() == 1 else 'add_reaction'
        else:
            if self.user in reaction.users.all():
                reaction.users.remove(self.user)
                action = 'delete_reaction' if reaction.users.count() == 0 else 'remove_reaction'
            else:
                reaction.users.add(self.user)
                action = 'add_reaction'

        send_data = {
            'action': action,
            'reaction_pk': reaction.pk,
            'sender': self.user.pk,
        }

        if action == 'create_reaction':
            send_data['html'] = render_to_string('rooms/elements/reaction.html', context={'reaction': reaction})
            send_data['backlog_pk'] = backlog_pk
        elif action == 'delete_reaction':
            reaction.delete()
        
        return send_data
    
    
    async def get_emote_menu(self, **kwargs):
        @sync_to_async
        def get_emote_menu():
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

            chat = self.get_chat()
            tooltip = render_to_string('rooms/tooltips/emotes-menu/emotes-menu.html', {'chat': chat})
            emoji_categories = [
                render_to_string('rooms/tooltips/emotes-menu/emoji-category.html', {'emoji_list': Emoji.objects.filter(category=category), 'category': category})
                for category in categories
            ]
            return tooltip, emoji_categories
        
        tooltip, emoji_categories = await get_emote_menu()
        await self.send(json.dumps({
            'action': 'build_emote_menu',
            'tooltip': tooltip,
            'emoji_categories': emoji_categories,
        }))

    async def send_reaction_to_client(self, event):
        send_data = {**event}
        sender = send_data.pop('sender')
        await self.send(text_data=json.dumps({
            'is_sender': (sender == self.user.pk),
            **send_data,
        }))


class GroupChatConsumer(AppConsumer, BacklogGroupUtils):    
    async def connect(self):
        await super().connect()
        group_chat_pk = self.scope["url_route"]['kwargs'].get('group_chat_pk')
        group_channel_pk = self.scope["url_route"]['kwargs'].get('group_channel_pk')
        self.group_chat = await db_async(lambda: GroupChat.objects.get(pk=group_chat_pk))
        await self.channel_layer.group_add(f'group_chat_{self.group_chat.pk}', self.channel_name)
        await self.channel_layer.group_add(f'group_chat_{self.group_chat.pk}_user_{self.user.pk}', self.channel_name)

        if not group_channel_pk:
            return
        
        self.group_channel = await db_async(lambda: GroupChannel.objects.get(pk=group_channel_pk))
        await self.create_common_attributes(self.group_channel)
        await self.channel_layer.group_add(f'group_channel_{self.group_channel.pk}', self.channel_name)
        await self.channel_layer.group_add(f'group_channel_{self.group_channel.pk}_user_{self.user.pk}', self.channel_name)
        await self.generate_backlogs()

    def get_chat(self):
        return self.group_chat

    async def get_mentionables(self, mention, **kwargs):
        alphanumeric, numeric = await process_mention(mention)
        html = await super().get_mentionables(self.group_chat, alphanumeric, numeric, kind='group_chat')
        await self.send(text_data=json.dumps({
            'action': 'get_mentionables',
            'html': html,
        }))

    async def create_message(self, content=None, file=None, **kwargs):
        if not content and not file:
            return

        backlog = await super().create_message(content=content, file=file)

        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}', {
                'type': 'send_message_to_client',
                'action': 'create_message',
                'pk': backlog.pk,
                'sender': self.user.pk,
            }
        )

        await self.channel_layer.group_send(
            f'backlog_group_{self.backlog_group.pk}', {
                'type': 'create_new_backlog_notification',
                'backlog': backlog.pk,
                'target_backlog_group': self.backlog_group.pk,
                'sender': self.user.pk,
                'notification_type': 'group_chat_notification',
                'group_channel': self.group_channel.pk,
                'group_chat': self.group_chat.pk,
            }
        )

    async def mark_as_read(self, **kwargs):
        reduce_notifications_by = await super().mark_as_read()
        if not reduce_notifications_by:
            return
        
        await self.channel_layer.group_send(
            f'user_{self.user.pk}', {
                'type': 'send_to_client',
                'action': 'remove_notification',
                'modifier': 'hidden',
                'times': reduce_notifications_by,
                'id': f'group-chat-{self.group_chat.pk}'
            }
        )
        
        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}_user_{self.user.pk}', {
                'type': 'send_to_client',
                'action': 'mark_as_read',
            }
        )

        await self.channel_layer.group_send(
            f'group_chat_{self.group_chat.pk}_user_{self.user.pk}', {
                'type': 'send_to_client',
                'action': 'remove_all_notifications',
                'id': f'group-channel-{self.group_channel.pk}'
            }
        )

    async def delete_backlog(self, pk, action, **kwargs):
        deleted = await super().delete_backlog(pk)
        if not deleted:
            return
        
        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}', {
                'type': 'send_to_client',
                'action': 'delete_backlog',
                'pk': pk
            }
        )

    async def edit_message(self, pk, content, action, **kwargs):
        if not content:
            return
        
        send_data = await super().edit_message(pk, content)
        if not send_data:
            return

        await self.channel_layer.group_send(f'group_channel_{self.group_channel.pk}', send_data)

    async def react_backlog(self, kind, emoticon_pk, backlog_pk, **kwargs):
        input_is_valid = await super().validate_react_backlog_input(kind, emoticon_pk, backlog_pk)
        if not input_is_valid:
            return
        
        send_data = await super().process_reaction(kind, emoticon_pk, backlog_pk)
        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}', {
                'type': 'send_reaction_to_client',
                **send_data
            }
        )

    async def leave_group_chat(self, **kwargs):
        @sync_to_async
        def leave_group_chat():
            membership = GroupChatMembership.objects.get(chat=self.group_chat, user=self.user)
            channel = self.group_chat.channels.first()
            backlog = Backlog.objects.create(kind='log', group=channel.backlog_group)
            log = Log.objects.create(backlog=backlog, action='leave', user1=self.user)
            membership.delete()

            return [
                self.channel_layer.group_send(
                    f'group_chat_{self.group_chat.pk}', {
                        'type': 'send_log_to_client',
                        'action': 'create_log',
                        'pk': backlog.pk,
                    }
                ),
                self.channel_layer.group_send(
                    f'user_{self.user.pk}', {
                        'type': 'send_to_client',
                        'action': 'leave_group_chat',
                        'pk': self.group_chat.pk,
                    }
                ),
                self.send(text_data=json.dumps({
                    'action': 'redirect',
                    'url': reverse('dashboard')
                })),
            ]
        
        for send in await leave_group_chat():
            await send


class PrivateChatConsumer(AppConsumer, BacklogGroupUtils):
    async def connect(self):
        await super().connect()
        private_chat_pk = self.scope["url_route"]['kwargs'].get('private_chat_pk')
        self.private_chat = await db_async(lambda: PrivateChat.objects.get(pk=private_chat_pk))
        await self.create_common_attributes(self.private_chat)
        await self.channel_layer.group_add(f'private_chat_{self.private_chat.pk}', self.channel_name)
        await self.channel_layer.group_add(f'private_chat_{self.private_chat.pk}_user_{self.user.pk}', self.channel_name)
        await self.generate_backlogs()

    def get_chat(self):
        return self.private_chat
    
    async def mark_as_read(self, **kwargs):
        reduce_notifications_by = await super().mark_as_read()
        if not reduce_notifications_by:
            return
        
        await self.channel_layer.group_send(
            f'user_{self.user.pk}_self', {
                'type': 'send_to_client',
                'action': 'remove_all_notifications',
                'id': f'private-chat-{self.private_chat.pk}'
            }
        )

        await self.channel_layer.group_send(
            f'private_chat_{self.private_chat.pk}_user_{self.user.pk}', {
                'type': 'send_to_client',
                'action': 'mark_as_read',
            }
        )
        
        await self.channel_layer.group_send(
            f'user_{self.user.pk}', {
                'type': 'send_to_client',
                'action': 'remove_notification',
                'times': reduce_notifications_by,
                'id': f'dashboard-button'
            }
        )

    async def create_message(self, content, file=None, **kwargs):
        @sync_to_async
        def users_to_activate():
            return [(membership.user, membership) for membership in self.private_chat.memberships.all() if membership.activate()]

        if not content:
            return
        
        backlog = await super().create_message(content)
        
        await self.channel_layer.group_send(
            f'private_chat_{self.private_chat.pk}', {
                'type': 'send_message_to_client',
                'action': 'create_message',
                'pk': backlog.pk,
                'sender': self.user.pk,
            }
        )
        
        for user, membership in await users_to_activate():
            await self.channel_layer.group_send(
                f'user_{user.pk}_self', {
                    'type': 'send_to_client',
                    'action': 'activate_private_chat',
                    'html': await sync_to_async(render_to_string)('rooms/elements/private-chat.html', {'local_private_chat': self.private_chat, 'other_party': {'user': self.user}})
                }
            )

        for user in await database_sync_to_async(self.private_chat.user_list)():
            await self.channel_layer.group_send(
                f'user_{user.pk}', {
                    'type': 'create_new_backlog_notification',
                    'backlog': backlog.pk,
                    'target_backlog_group': self.backlog_group.pk,
                    'sender': self.user.pk,
                    'notification_type': 'private_chat_notification',
                    'private_chat': self.private_chat.pk
                }
            )

    async def get_mentionables(self, mention, **kwargs):
        username, username_id = await process_mention(mention)
        html = await super().get_mentionables(self.private_chat, username, username_id, kind='private_chat')
        await self.send(text_data=json.dumps({
            'action': 'get_mentionables',
            'html': html,
        }))

    async def react_backlog(self, kind, emoticon_pk, backlog_pk, **kwargs):
        input_is_valid = await super().validate_react_backlog_input(kind, emoticon_pk, backlog_pk)
        if not input_is_valid:
            return
        
        send_data = await super().process_reaction(kind, emoticon_pk, backlog_pk)
        await self.channel_layer.group_send(
            f'private_chat_{self.private_chat.pk}', {
                'type': 'send_reaction_to_client',
                **send_data
            }
        )

    async def edit_message(self, pk, content, action, **kwargs):
        if not content:
            return
        
        send_data = await super().edit_message(pk, content)
        if not send_data:
            return

        await self.channel_layer.group_send(f'private_chat_{self.private_chat.pk}', send_data)

    async def delete_backlog(self, pk, action, **kwargs):
        deleted = await super().delete_backlog(pk)
        if not deleted:
            return
        
        await self.channel_layer.group_send(
            f'private_chat_{self.private_chat.pk}', {
                'type': 'send_to_client',
                'action': 'delete_backlog',
                'pk': pk
            }
        )