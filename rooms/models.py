from PIL import Image
from itertools import chain
from datetime import datetime

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation

from users.models import CustomUser


# *Room
class Room(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=60, blank=True)
    owner = models.ForeignKey(CustomUser, related_name='servers_owned', null=True, on_delete=models.SET_NULL)
    image = models.ImageField(default='blank.png', max_length=500)
    date_added = models.DateTimeField(auto_now_add=True)
    default_role = models.ForeignKey('Role', on_delete=models.CASCADE, related_name='+', null=True)

    def banned_users(self):
        return self.bans.all().filter(
            expiration_date__gt=datetime.now()
        ).values_list('user', flat=True)

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


# *RoomBan
class RoomBan(models.Model):
    room = models.ForeignKey(Room, related_name='bans', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name='bans', on_delete=models.CASCADE)
    expiration_date = models.DateTimeField()


# *Channel
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
    

# *ChannelCategory
class ChannelCategory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=30)
    order = models.PositiveIntegerField(default=1_000_000)
    
    def channels_by_order(self):
        return self.channels.all().order_by('order')
    
    def __str__(self):
        return f'{self.room}: {self.name} | order: {self.order}'
    

# *Role
class Role(models.Model):
    name = models.CharField(max_length=50, blank=False, default='Role')
    hierarchy = models.IntegerField(default=10)
    room = models.ForeignKey(Room, related_name='roles', on_delete=models.CASCADE, null=True)
    color = models.CharField(default='#e0dbd1', max_length=7)

    can_create_message = models.BooleanField(default=True)
    can_delete_lower_message = models.BooleanField(default=False)
    can_delete_higher_message = models.BooleanField(default=False)
    
    can_edit_lower_message = models.BooleanField(default=False)
    can_edit_higher_message = models.BooleanField(default=False)

    can_create_channel = models.BooleanField(default=False)
    can_edit_channel = models.BooleanField(default=False)
    can_delete_channel = models.BooleanField(default=False)

    can_view_channels = models.ManyToManyField(Channel, related_name='viewable_by_roles', blank=True)


# *Member
class Member(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, related_name='memberships')
    roles = models.ManyToManyField(Role, related_name='members')
    room = models.ForeignKey(Room, related_name='members', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=30, blank=True)
    
    def __str__(self):
        return f'{self.room.pk}: {self.user.__str__()}' +f'{self.nickname or ""}'
    
    def joined_site(self):
        return self.user.joined_site()
    
    def joined_room(self):
        return self.date_added.strftime("%d %B %Y")

    def display_name(self):
        return self.nickname or self.user.username
    
    def full_name(self):
        return self.user.full_name()
    
    def image(self):
        return self.user.image.url
    
    def bio(self):
        return self.user.bio


# *Message
class Message(models.Model):
    content = models.CharField(max_length=1000, blank=False)
    member = models.ForeignKey(Member, related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(CustomUser, related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.ForeignKey(Channel, related_name='messages', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    reactions = GenericRelation('Reaction', 'target_pk', 'target_type')

    class Meta:
        ordering = ('date_added',)
    
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")

    def __str__(self):
        return f'{self.pk} | user: {self.user} (pk: {self.user.pk}) | room: {self.channel.room.name} | channel: {self.channel.name}'

        
# *Action
class Action(models.Model):
    name = models.CharField(max_length=20)
    display_name = models.CharField(max_length=20)
    description = models.CharField(max_length=200, blank=True, null=True)
    icon = models.CharField(default='', max_length=30)

    def __str__(self):
        return f'{self.name}: {self.description}'


# *Log
class Log(models.Model):
    action = models.ForeignKey(Action, related_name='logs', on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, related_name='logs', on_delete=models.CASCADE, null=True)
    receiver = models.ForeignKey(CustomUser, related_name='received_actions', on_delete=models.SET_NULL, null=True)
    sender = models.ForeignKey(CustomUser, related_name='sent_actions', on_delete=models.SET_NULL, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True)
    reactions = GenericRelation('Reaction', 'target_pk', 'target_type')

    class Meta:
        ordering = ('date_added',)
        
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")


# *Emote
class Emote(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='emotes', blank=True, null=True)
    name = models.CharField(max_length=20)
    image = models.ImageField(max_length=500)

    # def save(self):
    #     super().save()
    #     img = Image.open(self.image.path)
    #     new_img = (24, 24)
    #     img.thumbnail(new_img)
    #     img.save(self.image.path)

    def __str__(self):
        return f'{self.name} | room: {self.room}'


# *Reaction
class Reaction(models.Model):
    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    target_pk = models.PositiveIntegerField(null=True)
    target_object = GenericForeignKey('target_type', 'target_pk')

    emote = models.ForeignKey(Emote, on_delete=models.CASCADE, null=True)
    users = models.ManyToManyField(CustomUser, blank=True)
    
    def add_user(self, user):
        self.users.add(user)
    
    def remove_user(self, user):
        self.users.remove(user)
        if len(self.users) == 0:
            self.delete()
    
    def image(self):
        return self.emote.image