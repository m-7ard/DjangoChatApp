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
)
from users.models import Friendship, CustomUser
from utils import get_object_or_none


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            return self.close()
        
        await self.channel_layer.group_add(f'user_{self.user.pk}', self.channel_name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        print('received: ', data)
        handler = getattr(self, data['action'])
        await handler(**data)
    
    async def disconnect(self, close_code):
        await self.close()

    async def send_to_client(self, event):
        print('sending', 'data: ', event)
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def async_db_operation(self, fn):
        return fn()
    

class GroupChatConsumer(ChatConsumer):
    async def connect(self):
        group_chat_pk = self.scope["url_route"]['kwargs'].get('group_chat_pk')
        group_channel_pk = self.scope["url_route"]['kwargs'].get('group_channel_pk')
        self.group_chat = await self.async_db_operation(lambda: get_object_or_none(GroupChat, pk=group_chat_pk))
        self.group_channel = await self.async_db_operation(lambda: get_object_or_none(GroupChannel, pk=group_channel_pk))
        await self.channel_layer.group_add(f'group_channel_{self.group_channel.pk}', self.channel_name)

        await super().connect()

    async def create_message(self, content, **kwargs):
        if not content:
            return
        
        backlog = await self.async_db_operation(lambda: Backlog.objects.create(kind='message', group=self.group_channel.backlog_group))
        message = await self.async_db_operation(lambda: Message.objects.create(user=self.user, content=content, backlog=backlog))
        html = render_to_string(template_name='rooms/elements/message.html', context={'backlog': backlog})

        await self.channel_layer.group_send(
            f'group_channel_{self.group_channel.pk}', {
                'type': 'send_to_client',
                'html': html,
                **kwargs
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
        self.chat = await self.async_db_operation(
            lambda: PrivateChatConsumer.objects.get(pk=chat_pk)
        )

        super().connect()
"""