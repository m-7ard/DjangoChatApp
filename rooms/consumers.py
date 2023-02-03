import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from django.contrib.auth.models import User
from .models import Message, Channel, Room, Log


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channelID = self.scope['url_route']['kwargs']['channel']
        self.channel_group_name = f'channel_{self.channelID}'
        self.user = self.scope['user']

        new_member = await self.add_to_members() # custom defined to add user to the channel's room.

        await self.channel_layer.group_add(
            self.channel_group_name,
            self.channel_name,
        )

        if new_member:
            date = new_member.display_date()
            action = new_member.action

            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    'type': 'chat_member_log',
                    'pattern': 'joined_channel',
                    'username': self.user.username,
                    'date': date,
                    'action': action,
                }
            )

        await self.accept()

    async def disconnect(self, response_code=None):
        await self.channel_layer.group_discard(
            self.channel_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data['content']
        username = data['username']
        channel = data['channel']

        message = await self.save_message(
            username=username, 
            channel=channel,
            content=content
            )
        date = message.display_date()

        await self.channel_layer.group_send(
            self.channel_group_name,
            {
                'type': 'chat_message',
                'pattern': 'sent_message',
                'content': content,
                'username': username,
                'channel': channel,
                'date': date,
            }
        )

    # Receive message from room group
    # executes this logic for every single user in the group
    async def chat_message(self, event):
        pattern = event['pattern']
        content = event['content']
        username = event['username']
        date = event['date']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'pattern': pattern, 
            'content': content,
            'username': username,
            'date': date,
        }))

    async def chat_member_log(self, event):
        pattern = event['pattern']
        action = event['action']
        username = event['username']
        date = event['date']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'pattern': pattern, 
            'action': action,
            'username': username,
            'date': date,
        }))

    @sync_to_async
    def save_message(self, username, channel, content):
        user = User.objects.all().get(username=username)
        channel = Channel.objects.all().get(id=channel)

        New_Message = Message(user=user, channel=channel, content=content)
        New_Message.save()
        
        return New_Message

    @sync_to_async
    def add_to_members(self):
        room = Room.objects.get(channels__id=self.channelID)
        user = self.user
        members = room.members
        
        if not members.filter(id=self.user.id).exists():
            members.add(user)
            New_Log = Log(user=user, room=room, action='Joined')
            New_Log.save()
            return New_Log
        
        return None


            