from PIL import Image
from itertools import chain

from django.db import models

from users.models import CustomUser



class Room(models.Model):
    name = models.CharField(max_length=50, blank=False)
    description = models.CharField(max_length=60, blank=True)
    owner = models.ForeignKey(CustomUser, related_name='servers_owned', null=True, on_delete=models.SET_NULL)
    image = models.ImageField(default='blank.png', max_length=500)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}'
    
    def display_date(self):
        return self.date_added.strftime("%d/%m/%Y")
    
    def members_by_users(self):
        return self.members.all()

    def members_by_status(self):
        online = self.members.all().filter(
            user__profile__status='online'
        )
        offline = self.members.all().difference(online)
        result = {
            'Online': online,
            'Offline': offline
        }
        return result

    def uncategorised(self):
        return self.channels.all().filter(category=None)


class Channel(models.Model):
    TEXT = 'text'
    VOICE = 'voice'
    KIND = (
        (TEXT, 'Text Channel'),
        (VOICE, 'Voice Channel'),
    )
    room = models.ForeignKey(Room, related_name='channels', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=30, blank=False)
    description = models.CharField(max_length=60, blank=True)
    display_logs = models.ManyToManyField('Action', blank=True)
    category = models.ForeignKey('ChannelCategory', on_delete=models.SET_NULL, related_name='channels', null=True, blank=True)
    kind = models.CharField(max_length=20, choices=KIND, default=TEXT)
    order = models.PositiveIntegerField(default=1_000_000)

    def __str__(self):
        return f'{self.room}: {self.name}'

    def display_actions(self):
        return [action.name for action in self.display_logs.all()]

    


    

class ChannelCategory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=30)
    order = models.PositiveIntegerField(default=1_000_000)
    
    def channels_by_order(self):
        return self.channels.all().order_by('order')
    
    def __str__(self):
        return f'{self.room}: {self.name} | order: {self.order}'
    

class Role(models.Model):
    name = models.CharField(max_length=50, blank=False, default='Role')
    hierarchy = models.IntegerField(default=10)
    room = models.ForeignKey(Room, related_name='roles', on_delete=models.CASCADE, null=True)
    color = models.CharField(default='#e0dbd1', max_length=7)

    can_create_message = models.BooleanField(default=True)
    can_delete_own_message = models.BooleanField(default=True)
    can_delete_lower_message = models.BooleanField(default=False)
    can_delete_higher_message = models.BooleanField(default=False)
    
    can_edit_own_message = models.BooleanField(default=True)
    can_edit_lower_message = models.BooleanField(default=False)
    can_edit_higher_message = models.BooleanField(default=False)

    can_create_channel = models.BooleanField(default=False)
    can_edit_channel = models.BooleanField(default=False)
    can_delete_channel = models.BooleanField(default=False)

    can_view_channels = models.ManyToManyField(Channel, related_name='viewable_by_roles', blank=True)


class Member(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, related_name='memberships')
    roles = models.ManyToManyField(Role, related_name='members')
    room = models.ForeignKey(Room, related_name='members', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=30, blank=True)
    
    def __str__(self):
        return self.user.__str__()
    
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")

    def display_name(self):
        return self.nickname or self.user.username
    
    def image(self):
        return self.user.profile.image.url



class Message(models.Model):
    content = models.CharField(max_length=1000, blank=False)
    member = models.ForeignKey(Member, related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(CustomUser, related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.ForeignKey(Channel, related_name='messages', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('date_added',)
    
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")

    def __str__(self):
        return f'{self.pk} | user: {self.user} (pk: {self.user.pk}) | room: {self.channel.room.name} | channel: {self.channel.name}'

        
class Action(models.Model):
    name = models.CharField(max_length=20)
    display_name = models.CharField(max_length=20)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.name}: {self.description}'


class Log(models.Model):
    action = models.ForeignKey(Action, related_name='logs', on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, related_name='logs', on_delete=models.CASCADE, null=True)
    target_user = models.ForeignKey(CustomUser, related_name='room_activity', on_delete=models.SET_NULL, null=True)
    trigger_user = models.ForeignKey(CustomUser, related_name='room_actions', on_delete=models.SET_NULL, null=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True)

    # if the action model were deleted, this would remain
    action_display_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ('date_added',)
        
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")
    
    def instance(self):
        return 'log'


class Reaction(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reactions', blank=True, null=True)
    name = models.CharField(max_length=20)
    image = models.ImageField()

    # def save(self):
    #     super().save()
    #     img = Image.open(self.image.path)
    #     new_img = (24, 24)
    #     img.thumbnail(new_img)
    #     img.save(self.image.path)

    def __str__(self):
        return f'{self.name} | room: {self.room}'

class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    users = models.ManyToManyField(CustomUser, blank=True)
    
    def add_user(self, user):
        self.users.add(user)
    
    def remove_user(self, user):
        self.users.remove(user)
        if len(self.users) == 0:
            self.delete()
    
    def image(self):
        return self.reaction.image
    
    def __str__(self):
        return f'{self.message.pk} | reaction: {self.reaction.name} | room: {self.message.channel.room.name}'