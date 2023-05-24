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
from django.contrib.auth.models import User
from django.http import HttpResponse

from DjangoChatApp.templatetags.custom_tags import convert_reactions
from .forms import MessageForm
from .models import (
    Message, 
    Channel, 
    Room, 
    Log, 
    Member, 
    Action, 
    Reaction, 
    MessageReaction
)
from users.models import Friendship

from utils import get_object_or_none, get_rendered_html
from DjangoChatApp.templatetags.custom_tags import get_friendship_friend

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print(self.scope)
        self.loop = asyncio.get_event_loop()
        self.user = self.scope['user']
        self.room, self.channel = None, None
        
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
        print('accepted')

        # Ping to see if the user is online
        # self.ping_task = asyncio.create_task(self.send_ping())
        # await self.update_user_status(self.user, 'online')

    async def disconnect(self, response_code=None):
        # if hasattr(self, 'ping_task'):
        #     self.ping_task.cancel()
        
        # user = await sync_to_async(User.objects.get)(pk=self.user.pk)
        # self.loop.create_task(self.async_user_check(user))
        # If I wanted to use it on the other thread
        # users_to_check.append(user)

        print('disconnect', response_code)

        await self.channel_layer.group_discard(
            'online_users',
            self.channel_name,
        )



        if self.channel:
            await self.channel_layer.group_discard(
                self.channel_group_name,
                self.channel_name,
            )
        if self.room:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        handlers = {
            # 'join': self.room_user_logs_delegator,
            # 'leave': self.room_user_logs_delegator,
            
            'send-message': self.send_message,
            'edit-message': self.edit_message,
            'delete-message': self.delete_message,
            'react-message': self.react_message,
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
        
    async def send_to_JS(self, event):
        print('sending', 'data: ', event)
        await self.send(text_data=json.dumps(event))
    
    """
    async def send_ping(self):
        while True:
            await self.send(text_data=json.dumps({'action': 'ping'}))
            await asyncio.sleep(10)
            if not self.ping:
                await self.disconnect()
                return
            
    async def receive_ping(self, data):
        await self.update_user_last_ping()
        print(f'ping updated at {self.user.profile.last_ping}')
        self.ping = True
    """

    @database_sync_to_async
    def react_message(self, data):
        reaction = get_object_or_none(Reaction, pk=data.get('reactionPk'))
        message = get_object_or_none(Message, pk=data.get('messagePk'))
        print(reaction, message)
        if not reaction or not message:
            return
        
        message_reaction, created = MessageReaction.objects.get_or_create(reaction=reaction, message=message)
        send_data = {**data}

        if self.user in message_reaction.users.all():
            message_reaction.users.remove(self.user)
            if len(message_reaction.users.all()) == 0:
                message_reaction.delete()
                send_data['actionType'] = 'deleteReaction'
            else:
                send_data['actionType'] = 'removeReaction'
        else:
            message_reaction.users.add(self.user)
            if created:
                send_data['actionType'] = 'createReaction'
                send_data['url'] = message_reaction.reaction.image.url
            else:
                send_data['actionType'] = 'addReaction'

        self.loop.create_task(
            self.channel_layer.group_send(
                self.channel_group_name, {
                'type': 'send_to_JS',
                'action': 'react_message',
                **send_data
                }
            )
        )

    """
    async def room_user_logs_delegator(self, data):
        async def join(data):
            @sync_to_async
            def user_joins():
                room = Room.objects.get(id=self.room_pk)
                user = self.user
                member, created = Member.objects.get_or_create(
                    room=room,
                    user=user
                )
                
                return created

            is_new_member = await user_joins()
            if is_new_member:
                action_name = 'room join'
                log = await create_log_DB(action_name)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_to_JS',
                        'action': 'log',
                        'action_display_name': log.action_display_name,
                        'trigger_user': log.trigger_user.username,
                        'date': log.display_date(),
                    }
                )
        
        async def leave(data):
            @sync_to_async
            def user_leaves():
                room = Room.objects.get(id=self.room_pk)
                user = self.user
                member = get_object_or_none(Member, room=room, user=user)
                exists = member is not None

                if exists:
                    member.delete()

                return exists
                
            is_already_member = await user_leaves()
            if is_already_member:
                log = await create_log_DB('room leave')
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_to_JS',
                        'action': 'log',
                        'action_display_name': log.action_display_name,
                        'trigger_user': log.trigger_user.username,
                        'date': log.display_date(),
                    }
                )

        @sync_to_async
        def create_log_DB(action_name, message_pk=None):
            room = Room.objects.get(id=self.room_pk)
            action = Action.objects.get(name=action_name)
            trigger_user = self.user
            target_user = Message.objects.get(pk=message_pk).user if message_pk else None

            if action_name == 'room join':
                date = Member.objects.get(user=trigger_user, room=room).date_added
            else:
                date = datetime.datetime.now().strftime("%H:%M:%S")

            log = Log.objects.create(
                room=room,
                trigger_user=trigger_user,
                target_user=target_user,
                action=action,
                date_added=date
            )

            return log
        
        handlers = {
            'join': join,
            'leave': leave,
        }

        action = data['action']
        handler = handlers.get(action)
        if handler:
            await handler(data)
    """

    @database_sync_to_async
    def send_message(self, data):
        member = get_object_or_none(Member, user=self.user, room=self.room)
        content = data['content']
        send_data = {**data}

        if member:
            message_form = MessageForm(data={
                'user': self.user, 
                'channel': self.channel, 
                'member': member, 
                'content': content
            })
                
            if message_form.is_valid():
                message = message_form.save()
                data = {
                    'room': self.room,
                    'user': self.user,
                    'object': message
                }
                message_html = get_rendered_html(
                    Path(__file__).parent / 'templates/rooms/elements/message.html', 
                    data
                )
                self.loop.create_task(
                    self.channel_layer.group_send(
                        self.channel_group_name, {
                        'type': 'send_to_JS',
                        'html': message_html,
                        **send_data
                        }
                    )
                )
                
    @database_sync_to_async
    def edit_message(self, data):
        member = get_object_or_none(Member, user=self.user, room=self.room)
        content = data['content']
        send_data = {**data}

        if member:
            instance = Message.objects.get(pk=data['messagePk'])
            form = MessageForm(data={
                'user': self.user, 
                'channel': self.channel, 
                'member': member, 
                'content': content
            }, instance=instance)
                
            if form.is_valid():
                message = form.save()
                send_data['content'] = convert_reactions(message.content, self.room.pk)
                
                self.loop.create_task(
                    self.channel_layer.group_send(
                        self.channel_group_name,
                        {
                        'type': 'send_to_JS',
                        'action': 'edit_message',
                        **send_data
                        }
                    )
                )

    @database_sync_to_async
    def delete_message(self, data):
        print(data.get('messagePk'))
        message = get_object_or_none(Message, pk=data.get('messagePk'))
        send_data = {**data}

        if message:
            message.delete()
            self.task_group_send(send_data)


    @database_sync_to_async
    def manage_friendship(self, data):
        kind = data['kind']
        friendship = get_object_or_none(Friendship, pk=data['friendshipPk'])
        send_data = {**data}

        if not friendship:
            return

        if kind == 'accept':
            friendship.status = 'accepted'
            friendship.save()
            send_data['category'] = 'all'
        elif kind == 'reject' or kind == 'remove':
            friendship.delete()
        else:
            raise ValueError('Invalid action. Valid actions are: "accept", "reject", "remove".')
    
        self.loop.create_task(self.channel_layer.group_send(
            self.channel_group_name,
            {
            'type': 'send_to_JS',
            'action': 'friendship',
            **send_data,
            }
        ))
    
    """
    
    Checks whether the user has completely left the site

    """
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

    def task_group_send(self, send_data):
        self.loop.create_task(self.channel_layer.group_send(
            self.channel_group_name,
            {
            'type': 'send_to_JS',
            **send_data
            }
        ))


"""
# Define a function to run in another thread
def my_thread_function():
    global users_to_check
    # Create an event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the event loop indefinitely
    while True:
        # Get the argument for the async function from a queue or some other source
        user_list_length = len(users_to_check)
        users = users_to_check[:user_list_length]
        users_to_check = users_to_check[user_list_length:]

        for user in users:
            task = loop.create_task(async_user_check(user))
            # Alternatively, you can use loop.create_task(task) instead of ensure_future
            # to schedule the task on the event loop

        # Run the event loop to process the tasks asynchronously
        loop.run_until_complete(asyncio.sleep(0))


# Create a new thread and start it
users_to_check = []
thread = threading.Thread(target=my_thread_function)
thread.start()
"""