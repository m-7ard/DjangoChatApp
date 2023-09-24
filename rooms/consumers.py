import json
import datetime
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.urls import reverse

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
from users.models import Friendship, CustomUser, Friend
from utils import get_object_or_none
from DjangoChatApp.templatetags.custom_tags import convert_mentions

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
                channels_sends = await self.send_group_chat_notification(group_chat=kwargs['group_chat'], group_channel=kwargs['group_channel'])
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
    def send_group_chat_notification(self, group_chat, group_channel):
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
                'pk': receiver_profile.pk,
                'was_receiver': False,
                **kwargs
            }
        )

        await self.channel_layer.group_send(
            f'user_{receiver_user.pk}_dashboard', {
                'type': 'send_to_client',
                'pk': sender_profile.pk,
                'was_receiver': True,
                **kwargs
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
            return new_backlogs.exclude(message__user=self.user).count()

        return 0
    
    @sync_to_async
    def is_mentioned(self, pk):
        backlog = Backlog.objects.get(pk=pk)
        return self.user in backlog.mentions.all()
    
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
        
        backlog.delete()
        return True

    @sync_to_async
    def create_message(self, content):
        backlog = Backlog.objects.create(kind='message', group=self.backlog_group)
        message = Message.objects.create(user=self.user, content=content, backlog=backlog)

        return backlog
    
    @sync_to_async
    def render_backlog(self, pk):
        backlog = Backlog.objects.get(pk=pk)
        if backlog.kind == 'message':
            return render_to_string('rooms/elements/message.html', {'backlog': backlog, 'user': self.user})
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
            'content': convert_mentions(content),
            'invites': backlog.message.process_invites(),
            'pk': pk,
        }

        return send_data
    
    @sync_to_async
    def create_common_attributes(self, chat):
        self.backlog_group = chat.backlog_group
        self.tracker = BacklogGroupTracker.objects.get(user=self.user, backlog_group=self.backlog_group)
        backlogs = self.backlog_group.backlogs.select_related('message__user', 'log__user1', 'log__user2').order_by('-pk')
        self.paginator = Paginator(backlogs, 20)
        self.current_page = self.paginator.get_page(1)

    async def generate_backlogs(self, **kwargs):
        if self.current_page == None:
            return
        
        backlogs = self.current_page.object_list
        html = await sync_to_async(render_to_string)(
            template_name='rooms/elements/backlogs.html',
            context={'backlogs': backlogs, 'user': self.user},
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
    def get_mentionables(self, chat, username, username_id):
        query = chat.memberships.filter(user__username__icontains=username)[:10] if username else chat.memberships.all()[:10]
        query = query.select_related('user')

        if username_id:
            # mention username id is substring of member formatted username id
            query = filter(lambda member: username_id in member.user.formatted_username_id(), query)

        html = render_to_string(template_name='commons/tooltips/mentionables-list.html', context={
            'members': [{
                'username': member.user.username, 
                'username_id': member.user.formatted_username_id(),
                'image': member.user.image.url,
            } for member in query],
            'roles': [{

            }]
        })

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

    async def get_mentionables(self, mention, **kwargs):
        username, username_id = await process_mention(mention)
        html = await super().get_mentionables(self.group_chat, username, username_id)
        await self.send(text_data=json.dumps({
            'action': 'get_mentionables',
            'html': html,
        }))

    async def create_message(self, content, **kwargs):
        if not content:
            return
        
        backlog = await super().create_message(content)

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

    async def create_message(self, content, **kwargs):
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
        html = await super().get_mentionables(self.private_chat, username, username_id)
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

"""
class AppConsumer(AsyncWebsocketConsumer):
    async def connect(self):




class ChannelConsumer(AppConsumer):
    async def connect(self):
        self.loop = asyncio.get_event_loop()
        self.user = self.scope.get('user')
        self.room = None
        self.channel = None
        
        room_pk = self.scope['url_route']['kwargs'].get('room')
        channel_pk = self.scope['url_route']['kwargs'].get('channel')

        if room_pk:
            self.room = await sync_to_async(get_object_or_none)(obj=Room, pk=room_pk)
            self.room_group_name = f'room_{room_pk}'

            # Users in a Room
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )

        if channel_pk:
            self.channel = await sync_to_async(get_object_or_none)(obj=Channel, pk=channel_pk)
            self.channel_group_name = f'channel_{channel_pk}'

            # Users in a Channel
            await self.channel_layer.group_add(
                self.channel_group_name,
                self.channel_name,
            )

        if self.user:
            self.user_group_name = f'user_{self.user.pk}'

            # User Tabs
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name,
            )

            # All Users
            await self.channel_layer.group_add(
                'online_users',
                self.channel_name,
            )

        await self.accept()

        # sends a signal to check the websocket is working
        if hasattr(self, 'channel_group_name'):
            self.loop.create_task(self.channel_layer.group_send(
                self.channel_group_name,
                {
                'type': 'send_to_JS',
                'action': 'requestServerResponse'
                }
            ))

        print('accepted')

    async def disconnect(self, response_code=None):
        print('disconnect', response_code)

        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        if hasattr(self, 'channel_group_name'):
            await self.channel_layer.group_discard(
                self.channel_group_name,
                self.channel_name
            )

        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

        await self.channel_layer.group_discard(
            'online_users',
            self.channel_name,
        )

    async def receive(self, text_data):
        handlers = {
            'send-message': self.send_message,
            'edit-message': self.edit_message,
            'delete-backlog': self.delete_backlog,
            'react': self.react,
            'manage-friendship': self.manage_friendship,

            # 'ping': self.receive_ping,
            'requestServerResponse': self.requestServerResponse,
        }

        data = json.loads(text_data)
        action = data.get('action')
        handler = handlers.get(action)
        print('-------' * 10)
        print(action)
        if handler:
            await handler(data)
        else:
            raise 'No such handler exists'
        
    async def requestServerResponse(self, data):
        await self.send_to_JS({
            'action': 'requestServerResponse'
        })


    @database_sync_to_async
    def delete_backlog(self, data):
        object_type = data['objectType']
        if object_type == 'message':
            object_model = Message
        elif object_type == 'log':
            object_model = Log
        else:
            raise ValueError('objectType not defined in consumer delete_backlog method')

        object_ = get_object_or_none(object_model, pk=data['objectPk'])
        if object_:
            object_.delete()

        send_data = {**data}    
        self.task_group_send(send_data, self.channel_group_name)
        



    @database_sync_to_async
    def join_room(self, data):
        pass


    @database_sync_to_async
    def react(self, data):
        client_context = json.loads(data['context'])
        objects = client_context['objects']

        emote_pk = data.get('emotePk')
        object_model_name = objects['object'].get('model')
        object_app_label = objects['object'].get('app')
        object_pk = objects['object'].get('pk')
        model = apps.get_model(app_label=object_app_label, model_name=object_model_name)

        object_ = get_object_or_none(model, pk=object_pk)
        emote = get_object_or_none(Emote, pk=emote_pk)

        if not emote or not object_:
            return
        
        reaction, created = Reaction.objects.get_or_create(
            target_type=ContentType.objects.get_for_model(model), 
            target_pk=object_pk, 
            emote=emote
        )

        send_data = {
            'action': data['action'],
            **objects['object'],
            'emotePk': emote_pk,
        }

        if self.user in reaction.users.all():
            reaction.users.remove(self.user)
            if len(reaction.users.all()) == 0:
                reaction.delete()
                send_data['actionType'] = 'deleteReaction'
            else:
                send_data['actionType'] = 'removeReaction'
        else:
            reaction.users.add(self.user)
            if created:
                send_data['actionType'] = 'createReaction'
                send_data['imageUrl'] = reaction.emote.image.url
            else:
                send_data['actionType'] = 'addReaction'

        self.loop.create_task(self.channel_layer.group_send(
            self.channel_group_name,
            {
            'type': 'send_to_JS',
            **send_data
            }
        ))


    @database_sync_to_async
    def send_message(self, data):
        pass
                

    @database_sync_to_async
    def edit_message(self, data):
        pass


    @database_sync_to_async
    def delete_message(self, data):
        print(data.get('messagePk'))
        message = get_object_or_none(Message, pk=data.get('messagePk'))
        send_data = {**data}

        if message:
            message.delete()
            self.task_group_send(send_data, self.channel_group_name)


    @database_sync_to_async
    def manage_friendship(self, data):
        client_context = json.loads(data.pop('context'))
        objects = client_context['objects']
        
        friend = dict_to_object(objects['user'])
        kind = data.get('kind')

        if kind == 'send-friendship':
            friendship, created = Friendship.objects.get_or_create(sender=self.user, receiver=friend, status='pending')
        elif kind == 'accept-friendship':
            friendship = Friendship.objects.get(sender=friend, receiver=self.user)
            friendship.status = 'accepted'
            friendship.save()
        elif kind in {'reject-friendship', 'delete-friendship', 'cancel-friendship'}:
            friendship = Friendship.objects.filter(Q(sender=friend) | Q(receiver=friend)).first()
            friendship.delete()
            
    
    async def async_user_check(self, user):
        @sync_to_async
        def get_last_ping(user):
            return user.profile.last_ping
        
        # Wait for 30 seconds
        await asyncio.sleep(30)
        
        # Check the user's last response time
        last_response_time = await get_last_ping(user)
        time_barrier = timezone.make_aware(datetime.datetime.now() - datetime.timedelta(seconds=10), timezone.get_default_timezone())
        print(f'last ping: {last_response_time}')
        print(f'current time: {timezone.now()}')
        print(f'barrier time: {time_barrier}')
        if (last_response_time < time_barrier):
            print('user should be offline')
            await self.channel_layer.group_send(
                'online_users',
                {
                    'type': 'send_to_JS',
                    'action': 'offline',
                    'user': user.pk,
                }
            ) 
        else:
            self.update_user_status(self.user, 'offline')
            print('user is online')

    def task_group_send(self, send_data, group_name):
        print("Sending group message:", send_data)  # Add this line

        self.loop.create_task(self.channel_layer.group_send(
            group_name,
            {
            'type': 'send_to_JS',
            **send_data
            }
        ))


class PrivateChatConsumer(AppConsumer):
    async def connect(self):
        chat_pk = self.scope['url_route']['kwargs'].get('room')
        self.chat = await db_async(
            lambda: PrivateChatConsumer.objects.get(pk=chat_pk)
        )

        super().connect()
"""