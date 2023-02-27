import json
import datetime


from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

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
from users.models import (
    ConnectionHistory,
    UserTab
)

from utils import get_object_or_none

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room')
        self.channel_id = self.scope['url_route']['kwargs'].get('channel')
        self.user = self.scope['user']
        self.session = self.scope['session']

        self.room_group_name = f'room_{self.room_id}'
        self.channel_group_name = f'channel_{self.channel_id}'

        if self.channel_id:
            await self.channel_layer.group_add(
                self.channel_group_name,
                self.channel_name,
            )
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()
        await self.update_user_status(self.user, self.session, 'online')

    async def disconnect(self, response_code=None):
        print(self.tab.pk)
        await self.update_user_status(self.user, self.session, 'offline')

        if self.channel_id:
            await self.channel_layer.group_discard(
                self.channel_group_name,
                self.channel_name,
            )
        
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
        }
        data = json.loads(text_data)
        action = data['action']
        handler = handlers.get(action)
        if handler:
            await handler(data)
        else:
            raise 'No such handler'
            
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
            self.room_group_name,
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
        
    async def add_or_remove_reaction_DOM(self, event):
        await self.send(text_data=json.dumps(event))

    async def room_user_logs_delegator(self, data):
        async def join(data):
            @sync_to_async
            def user_joins():
                room = Room.objects.get(id=self.room_id)
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
                room = Room.objects.get(id=self.room_id)
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
            room = Room.objects.get(id=self.room_id)
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
            user = User.objects.get(id=user)
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

    async def send_to_JS(self, event):
        await self.send(text_data=json.dumps(event))
        

    @database_sync_to_async
    def update_user_status(self, user, session, status):
        connection, created = ConnectionHistory.objects.get_or_create(
            user=user, 
            session=session.session_key,
        )
        
        if status == 'online':
            tab = UserTab.objects.create(
                user=user,
                connection=connection,
            )
            self.send_to_JS(
                {
                    'action': 'tab',
                    'pk': tab.pk,
                }
            )
            self.tab = tab
        else:
            self.tab.delete()

        connection.status = status
        connection.save()





            

