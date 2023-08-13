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


@database_sync_to_async
def get_foreign_keys(name, *objects):
    return [getattr(object_, name) for object_ in objects]

@database_sync_to_async
def get_foreign_key(name, object_):
    return getattr(object_, name)

@database_sync_to_async
def db_async(fn):
    return fn()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        self.loop = asyncio.get_event_loop()

        if not self.user or not self.user.is_authenticated:
            return self.close()

        await self.create_extra_path()
        await self.channel_layer.group_add(f'user_{self.user.pk}', self.channel_name)
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
        """ Server-Side called method """
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
            Server-Side called method.
            Called from group send.
        """
        @database_sync_to_async
        def allow_notification(sender: int, target_backlog_group: int, backlog: int, **kwargs):
            consumer_backlog_group = getattr(self, 'backlog_group', None)
            consumer_backlog_group_pk = consumer_backlog_group.pk if consumer_backlog_group else None

            # backlog was sent by the same user
            is_sender = (sender == self.user.pk)
            if is_sender:
                return False

            # consumer user is already in the backlog_group's chat / channel; doesn't need a notification
            already_served = (consumer_backlog_group_pk == target_backlog_group)
            if already_served:
                return False
            
            # the user already saw the message
            target_backlog_group_tracker = BacklogGroupTracker.objects.get(user=self.user, backlog_group=target_backlog_group)
            last_backlog = target_backlog_group_tracker.last_backlog_seen
            last_backlog_pk = last_backlog.pk if last_backlog else None
            already_seen_backlog = (last_backlog_pk >= backlog)
            if already_seen_backlog:
                return False

            return True
        
        async def delegate_notification_creation(notification_type: str, target_backlog_group: int, **kwargs):
            await asyncio.sleep(2)
            if not await allow_notification(**event):
                return
            
            if notification_type == 'private_chat_notification':
                await self.send_private_chat_notification(backlog_group=target_backlog_group, private_chat=kwargs['private_chat'])
        
        self.loop.create_task(delegate_notification_creation(**event))
        
    async def send_private_chat_notification(self, backlog_group, private_chat):
        """ Server-Side called method """
        receiver = await db_async(lambda: PrivateChatMembership.objects.get(chat__backlog_group=backlog_group, user=self.user))
        # The private chat will now appear on the clients /self/... sidebar
        toggled = await db_async(lambda: receiver.activate())
        
        if 'self' in self.extra_path and toggled:
            html = await db_async(lambda: render_to_string(template_name='rooms/elements/message.html', context={
                'local_private_chat': receiver.chat, 
                'other_party': receiver
            })) 
            await self.send_to_client({
                'action': 'create_private_chat',
                'html': html
            })

        if 'self':
            await self.send_to_client({
                'action': 'create_notification',
                'id': f'private-chat-{private_chat}'
            })

        await self.send_to_client({
            'action': 'create_notification',
            'id': f'dashboard-button'
        })

    async def connect_user_to_chats(self):
        """ 
            Server-Side called method.
            This method makes the user listen to all backlogs groups they're in.
        """
        # using list(...) due to queryset not being iterable in async context
        user_backlog_groups = await db_async(
            lambda: list(self.user.backlog_trackers.values_list('backlog_group', flat=True))
        )
        for backlog_group in user_backlog_groups:
            await self.channel_layer.group_add(f'backlog_group_{backlog_group}', self.channel_name)
    
    async def accept_friendship(self, pk, **kwargs):
        """ Client-Side called method """
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
        """ Client-Side called method """
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

    @database_sync_to_async
    def confirm_backlog_reception(self, pk=None, **kwargs):
        """ Client-Side called method """
        # verify input integrity
        backlog = get_object_or_none(Backlog, pk=pk)
        if not backlog or backlog.group != self.backlog_group:
            return
        
        backlog_group_tracker = BacklogGroupTracker.objects.get(user=self.user, backlog_group=self.backlog_group)
        backlog_group_tracker.last_backlog_seen = backlog
        backlog_group_tracker.save()

    @database_sync_to_async
    def get_unread_backlog_count(self):
        if self.tracker.last_backlog_seen:
            unread_count = self.backlog_group.backlogs.filter(date_created__gt=self.tracker.last_backlog_seen.date_created).count()
        else:
            unread_count = self.backlog_group.backlogs.all().count()
        
        return unread_count

    @database_sync_to_async
    def update_last_backlog_seen(self):
        """ Server and Client-Side called method """
        self.tracker.last_backlog_seen = self.backlog_group.backlogs.last()
        self.tracker.save()

       
class GroupChatConsumer(ChatConsumer):    
    async def connect(self):
        await super().connect()
        group_chat_pk = self.scope["url_route"]['kwargs'].get('group_chat_pk')
        group_channel_pk = self.scope["url_route"]['kwargs'].get('group_channel_pk')
        self.group_chat = await db_async(lambda: GroupChat.objects.get(pk=group_chat_pk))
        await self.channel_layer.group_add(f'group_chat_{self.group_chat.pk}', self.channel_name)

        if not group_channel_pk:
            return
        
        self.group_channel = await db_async(lambda: GroupChannel.objects.get(pk=group_channel_pk))
        self.backlog_group = await get_foreign_key('backlog_group', self.group_channel)
        self.tracker = await db_async(lambda: BacklogGroupTracker.objects.get(user=self.user, backlog_group=self.backlog_group))
        await self.channel_layer.group_add(f'group_channel_{self.group_channel.pk}', self.channel_name)

    async def create_message(self, content, **kwargs):
        if not content:
            return
        
        backlog = await db_async(lambda: Backlog.objects.create(kind='message', group=self.group_channel.backlog_group))
        message = await db_async(lambda: Message.objects.create(user=self.user, content=content, backlog=backlog))
        html = render_to_string(template_name='rooms/elements/message.html', context={'backlog': backlog})

        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}', {
                'type': 'send_to_client',
                'html': html,
                **kwargs
            }
        )

    async def update_last_backlog_seen(self, **kwargs):
        super().update_last_backlog_seen()

        # write notification group sends here

        """
        
        TODO: notifications in groupchats at time of message creation
        
        """

class PrivateChatConsumer(ChatConsumer):
    async def connect(self):
        await super().connect()
        private_chat_pk = self.scope["url_route"]['kwargs'].get('private_chat_pk')
        self.private_chat = await db_async(lambda: PrivateChat.objects.get(pk=private_chat_pk))
        self.backlog_group = await get_foreign_key('backlog_group', self.private_chat)
        self.tracker = await db_async(lambda: BacklogGroupTracker.objects.get(user=self.user, backlog_group=self.backlog_group))
        await self.channel_layer.group_add(f'private_chat_{self.private_chat.pk}', self.channel_name)
        await self.update_last_backlog_seen()
    
    async def update_last_backlog_seen(self, **kwargs):
        unread_count = await super().get_unread_backlog_count()
        if not unread_count:
            return
        
        await super().update_last_backlog_seen()
        await self.channel_layer.group_send(
            f'user_{self.user.pk}_self', {
                'type': 'send_to_client',
                'action': 'remove_all_notifications',
                'id': f'private-chat-{self.private_chat.pk}'
            }
        )
        await self.channel_layer.group_send(
            f'user_{self.user.pk}', {
                'type': 'send_to_client',
                'action': 'remove_notification',
                'times': unread_count,
                'id': f'dashboard-button'
            }
        )

    async def create_message(self, content, **kwargs):
        if not content:
            return
        
        backlog = await database_sync_to_async(lambda: Backlog.objects.create(kind='message', group=self.private_chat.backlog_group))()
        backlog_group = await get_foreign_key('group', backlog)
        message = await database_sync_to_async(lambda: Message.objects.create(user=self.user, content=content, backlog=backlog))()
        html = render_to_string(template_name='rooms/elements/message.html', context={'backlog': backlog})

        await self.channel_layer.group_send(
            f'private_chat_{self.private_chat.pk}', {
                'type': 'send_to_client',
                'html': html,
                'pk': backlog.pk,
                **kwargs
            }
        )

        await self.channel_layer.group_send(
            f'backlog_group_{self.backlog_group.pk}', {
                'type': 'create_new_backlog_notification',
                'backlog': backlog.pk,
                'target_backlog_group': backlog_group.pk,
                'sender': self.user.pk,
                'notification_type': 'private_chat_notification',
                'private_chat': self.private_chat.pk
            }
        )







"""
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):




class ChannelConsumer(ChatConsumer):
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


class PrivateChatConsumer(ChatConsumer):
    async def connect(self):
        chat_pk = self.scope['url_route']['kwargs'].get('room')
        self.chat = await db_async(
            lambda: PrivateChatConsumer.objects.get(pk=chat_pk)
        )

        super().connect()
"""