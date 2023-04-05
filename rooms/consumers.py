import json
import datetime
import asyncio
import threading

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.utils import timezone

from django.contrib.auth.models import User

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

from utils import get_object_or_none


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.loop = asyncio.get_event_loop()
        self.ping = False

        self.user = self.scope['user']
        self.session = self.scope['session']

        self.room_pk = self.scope['url_route']['kwargs'].get('room')
        self.channel_pk = self.scope['url_route']['kwargs'].get('channel')

        self.room_group_name = f'room_{self.room_pk}'
        self.channel_group_name = f'channel_{self.channel_pk}'
        self.user_group_name = f'user_{self.user.pk}'

        # Users in a Channel
        if self.channel_pk:
            await self.channel_layer.group_add(
                self.channel_group_name,
                self.channel_name,
            )

        # User Tabs
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name,
        )

        # Users in a Room
        if self.room_pk:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )

        # All Users
        await self.channel_layer.group_add(
            'online_users',
            self.channel_name,
        )

        await self.accept()

        # Ping to see if the user is online
        self.ping_task = asyncio.create_task(self.send_ping())

        await self.update_user_status(self.user, 'online')

    async def disconnect(self, response_code=None):
        global users_to_check

        if hasattr(self, 'ping_task'):
            self.ping_task.cancel()
        
        user = await sync_to_async(User.objects.get)(pk=self.user.pk)
        self.loop.create_task(self.async_user_check(user))
        # If I wanted to use it on the other thread
        # users_to_check.append(user)

        await self.channel_layer.group_discard(
            'online_users',
            self.channel_name,
        )


        

        if self.channel_pk:
            await self.channel_layer.group_discard(
                self.channel_group_name,
                self.channel_name,
            )
        if self.room_pk:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

        
            
    async def receive(self, text_data):
        handlers = {
            'join': self.room_user_logs_delegator,
            'leave': self.room_user_logs_delegator,
            'message': self.message,
            'delete': self.delete,
            'react': self.react,
            'ping': self.receive_ping,
            'requestServerResponse': self.requestServerResponse,
        }
        data = json.loads(text_data)
        action = data['action']
        handler = handlers.get(action)
        if handler:
            await handler(data)
        else:
            raise 'No such handler'
        
    async def requestServerResponse(self, data):
        @database_sync_to_async
        def get_users():
            room = Room.objects.get(id=self.room_pk)
            online_members = room.members.filter(
                user__profile__status='online'
            )
            
            return online_members
        
        online_members = await get_users()
        

    async def send_to_JS(self, event):
        print('sending', 'data: ', event)
        await self.send(text_data=json.dumps(event))
    
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
            
    async def react(self, data):
        @sync_to_async
        def add_or_remove_reaction_DB(message_pk, reaction_pk):
            message = Message.objects.get(pk=message_pk)
            reaction = Reaction.objects.get(pk=reaction_pk)
            message_reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                reaction=reaction,
            )

            if user in message_reaction.users.all():
                message_reaction.users.remove(user)
                if len(message_reaction.users.all()) == 0:
                    modifier = 'delete'
                    message_reaction.delete()
                else:
                    modifier = 'remove'
            else:
                message_reaction.users.add(user)
                if created:
                    modifier = 'create'
                else:
                    modifier = 'add'
                
            image_url = message_reaction.reaction.image.url or None
            return (image_url, modifier)
        
        user = self.user
        message_pk = data['message_pk']
        reaction_pk= data['reaction_pk']
        image_url, modifier = await add_or_remove_reaction_DB(message_pk=message_pk, reaction_pk=reaction_pk)

        await self.channel_layer.group_send(
            self.channel_group_name,
            {
                'type': 'send_to_JS',
                'action': 'react',
                'message_pk': message_pk,
                'reaction_pk': reaction_pk,
                'user_pk': user.pk,
                'image_URL': image_url,
                'modifier': modifier,
            }
        )


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

    async def message(self, data):
        @sync_to_async
        def save_message_DB(user, channel, content):
            channel = Channel.objects.get(id=channel)
            user = User.objects.get(pk=user)
            member = get_object_or_none(Member, user=user, room=channel.room)
            
            if member:
                form = MessageForm(data={
                    'user': user, 
                    'channel': channel, 
                    'member': member, 
                    'content': content
                })
                if form.is_valid():
                    New_Message = form.save()
                    return New_Message

        user = data['user']
        channel = data['channel']
        content = data['content']

        message = await save_message_DB(
            user=user,
            channel=channel,
            content=content,
        )

        if message:
            date = message.display_date()
            username = message.member.nickname or message.user.username
            pk = message.pk
            
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                'type': 'send_to_JS',
                'action': 'message',
                'content': content,
                'username': username,
                'channel': channel,
                'date': date,
                'pk': pk,
                }
            )

    async def delete(self, data):
        @sync_to_async
        def delete_message_DB(pk):
            message = get_object_or_none(Message, pk=pk)
            if message:
                message.delete()
                return True

        pk = data['pk']
        deleted = await delete_message_DB(
            pk=pk
        )

        if deleted:
            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'send_to_JS',
                    'action': 'delete',
                    'pk': pk
                }
            ) 
        

    @database_sync_to_async
    def update_user_last_ping(self):
        self.user.profile.last_ping = datetime.datetime.now()
        self.user.profile.save()
    
    @database_sync_to_async
    def get_user_last_ping(self):
        return self.user.profile.last_ping
    
    @database_sync_to_async
    def update_user_status(self, user, status):
        user.profile.status = status

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