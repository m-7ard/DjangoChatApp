import json
import datetime
import asyncio
import threading
from pathlib import Path

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.utils import timezone
from django.template import Template, Context
from django.http import HttpResponse
from django.apps import apps
from django.template.loader import render_to_string
from django.core.paginator import Paginator


from .models import (
    Backlog,
    GroupChat,
    GroupChannel,
    Message,
    PrivateChat,
    BacklogGroupTracker,
    PrivateChatMembership
)
from users.models import Friendship, CustomUser, Friend
from utils import get_object_or_none

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
    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            return self.close()

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
        """ 
            Called from group send.
        """
        @database_sync_to_async
        def allow_notification(sender: int, target_backlog_group: int, backlog: int, **kwargs):
            # backlog was sent by the same user
            is_sender = (sender == self.user.pk)
            if is_sender:
                return False
            
            # the user already saw the message
            target_backlog_group_tracker = BacklogGroupTracker.objects.get(user=self.user, backlog_group=target_backlog_group)
            last_backlog = target_backlog_group_tracker.last_backlog_seen
            last_backlog_pk = last_backlog.pk if last_backlog else None
            already_seen_backlog = last_backlog_pk and (last_backlog_pk >= backlog)
            if already_seen_backlog:
                return False

            return True
        
        async def delegate_notification_creation(notification_type: str, target_backlog_group: int, **kwargs):
            await asyncio.sleep(2)
            if not await allow_notification(**event):
                return
            
            if notification_type == 'private_chat_notification':
                await self.send_private_chat_notification(backlog_group=target_backlog_group, private_chat=kwargs['private_chat'])
            elif notification_type == 'group_chat_notification':
                await self.send_group_chat_notification(group_chat=kwargs['group_chat'], group_channel=kwargs['group_channel'])
        
        self.loop.create_task(delegate_notification_creation(**event))
        
    async def send_private_chat_notification(self, backlog_group, private_chat):
        receiver = await db_async(lambda: PrivateChatMembership.objects.get(chat__backlog_group=backlog_group, user=self.user))
        # The private chat will now appear on the clients /self/... left side sidebar
        toggled = await db_async(lambda: receiver.activate())
        
        if 'self' in self.extra_path and toggled:
            html = await sync_to_async(render_to_string)(template_name='rooms/elements/message.html', context={
                'local_private_chat': get_foreign_key('chat', receiver), 
                'other_party': receiver
            })
            await self.send_to_client({
                'action': 'create_private_chat',
                'html': html
            })

        if 'self' in self.extra_path:
            await self.send_to_client({
                'action': 'create_notification',
                'id': f'private-chat-{private_chat}',
                'modifier': 'private-chat'
            })

        await self.send_to_client({
            'action': 'create_notification',
            'id': f'dashboard-button',
            'modifier': 'dashboard'
        })
    
    async def send_group_chat_notification(self, group_chat, group_channel):
        if hasattr(self, 'group_chat'):
            await self.send_to_client({
                'action': 'create_notification',
                'id': f'group-channel-{group_channel}',
                'modifier': 'hidden'
            })

        await self.send_to_client({
            'action': 'create_notification',
            'id': f'group-chat-{group_chat}',
            'modifier': 'hidden'
        })

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
    
    async def send_message_to_client(self, event):
        await self.send(text_data=json.dumps({
            'action': event['action'],
            'html': event['html'],
            'pk': event['pk'],
            'is_sender': (event['sender'] == self.user.pk)
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
        html = render_to_string(template_name='rooms/elements/message.html', context={'backlog': backlog})

        return backlog, html
    
    @sync_to_async
    def edit_message(self, pk, content):
        backlog = get_object_or_none(Backlog, pk=pk)
        if not backlog or backlog.group != self.backlog_group:
            return False
        
        message = backlog.message
        message.content = content
        message.save()
        return True
    
    async def generate_backlogs(self):
        @sync_to_async
        def get_backlogs():
            pass
    
    @sync_to_async
    def create_common_attributes(self, chat):
        self.backlog_group = chat.backlog_group
        self.tracker = BacklogGroupTracker.objects.get(user=self.user, backlog_group=self.backlog_group)
        backlogs = self.backlog_group.backlogs.select_related('message__user', 'log__receiver', 'log__sender').order_by('-pk')
        print(backlogs.explain())
        self.paginator = Paginator(backlogs, 20)
        self.current_page = self.paginator.get_page(1)

    async def generate_backlogs(self, **kwargs):
        if self.current_page == None:
            return
        
        backlogs = self.current_page.object_list
        html = await sync_to_async(render_to_string)(
            template_name='rooms/elements/backlogs.html',
            context={'backlogs': backlogs},
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

    async def get_mentionables(self, mention, uuid, positioning, **kwargs):
        username, username_id = await process_mention(mention)
        html = await super().get_mentionables(self.group_chat, username, username_id)
        await self.send(text_data=json.dumps({
            'action': 'get_mentionables',
            'html': html,
            'uuid': uuid,
            'positioning': positioning,
        }))

    async def create_message(self, content, **kwargs):
        if not content:
            return
        
        backlog, html = await super().create_message(content)

        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}', {
                'type': 'send_message_to_client',
                'html': html,
                'pk': backlog.pk,
                'sender': self.user.pk,
                **kwargs
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
        """
        
        TODO: fix error where the mark_as_read doesn't trigger when we generate backlogs at the first connection
        
        """
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
        
        edited = await super().edit_message(pk, content)
        if not edited:
            return
        
        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}', {
                'type': 'send_to_client',
                'action': 'edit_message',
                'content': content,
                'pk': pk,
            }
        )
        



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
        if not content:
            return
        
        backlog, html = await super().create_message(content)

        await self.channel_layer.group_send(
            f'private_chat_{self.private_chat.pk}', {
                'type': 'send_message_to_client',
                'html': html,
                'pk': backlog.pk,
                'sender': self.user.pk,
                **kwargs
            }
        )

        await self.channel_layer.group_send(
            f'backlog_group_{self.backlog_group.pk}', {
                'type': 'create_new_backlog_notification',
                'backlog': backlog.pk,
                'target_backlog_group': self.backlog_group.pk,
                'sender': self.user.pk,
                'notification_type': 'private_chat_notification',
                'private_chat': self.private_chat.pk
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