from itertools import chain
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import Permission
from django.core.validators import MaxValueValidator, MinValueValidator

from users.models import CustomUser


# *ChatterGroup
class ChatterGroup(models.Model):
    pass


# *RoleGroup
class RoleGroup(models.Model):
    pass


# *BacklogGroup
class BacklogGroup(models.Model):
    def items(self):
        return chain(self.logs.all(), self.messages.all())


# *ReactionGroup
class ReactionGroup(models.Model):
    pass


# *ChannelGroup
class ChannelGroup(models.Model):
    pass


# *Chatter
class Chatter(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='chatters', null=True)


# *Role
class Role(models.Model):
    name = models.CharField(max_length=50, blank=False, default='Role')
    hierarchy = models.IntegerField(default=10)
    color = models.CharField(default='#e0dbd1', max_length=7)
    admin = models.BooleanField(default=False)

    def __str__(self):
        return f'role: {self.pk}'


class ChatterProfileQuerySet(models.QuerySet):
    def online(self):
        return self.filter(user__status='online')
    
    def offline(self):
        return self.filter(user__status='offline')
    

# *ChatterProfile
class ChatterProfile(models.Model):
    chatter = models.OneToOneField(Chatter, on_delete=models.CASCADE, related_name='profile')
    roles = models.OneToOneField(RoleGroup, on_delete=models.PROTECT, related_name='+', null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=30, blank=True)

    objects = ChatterProfileQuerySet.as_manager()

    def __str__(self):
        return f'{self.room.pk}: {self.user.__str__()}' +f'{self.nickname or ""}'


# *Room
class Room(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True)
    image = models.ImageField(default='blank.png', max_length=500)
    date_created = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=False)

    owner = models.ForeignKey(Chatter, related_name='+', null=True, on_delete=models.SET_NULL)
    default_role = models.OneToOneField(Role, on_delete=models.CASCADE, related_name='+', null=True)
    chatters = models.OneToOneField(ChatterGroup, on_delete=models.PROTECT, related_name='room', null=True)
    roles = models.OneToOneField(RoleGroup, on_delete=models.PROTECT, related_name='room', null=True)
    channels = models.OneToOneField(ChannelGroup, on_delete=models.PROTECT, related_name='room', null=True)


# *RolePermissions
class RolePermissions(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions', null=True)
    CHOICES = (
        ('True', 'True'),
        ('False', 'False'),
        ('Null', 'Null')
    )
    add_message = models.CharField(max_length=10, choices=CHOICES, default='True') 
    delete_message = models.CharField(max_length=10, choices=CHOICES, default='True') 
    view_message = models.CharField(max_length=10, choices=CHOICES, default='True') 
    view_channel = models.CharField(max_length=10, choices=CHOICES, default='True') 
    add_reaction = models.CharField(max_length=10, choices=CHOICES, default='True') 
    attach_image = models.CharField(max_length=10, choices=CHOICES, default='True') 
    change_nickname = models.CharField(max_length=10, choices=CHOICES, default='True') 
    manage_nicknames = models.CharField(max_length=10, choices=CHOICES, default='False') 
    manage_channel = models.CharField(max_length=10, choices=CHOICES, default='False') 
    manage_role = models.CharField(max_length=10, choices=CHOICES, default='False') 
    change_room = models.CharField(max_length=10, choices=CHOICES, default='False') 
    mention_all = models.CharField(max_length=10, choices=CHOICES, default='True') 
    pin_message = models.CharField(max_length=10, choices=CHOICES, default='False') 
    kick_user = models.CharField(max_length=10, choices=CHOICES, default='False') 
    ban_user = models.CharField(max_length=10, choices=CHOICES, default='False') 
    read_logs = models.CharField(max_length=10, choices=CHOICES, default='False') 


# *BacklogContainer
class BacklogContainer(models.Model):
    backlogs = models.OneToOneField(BacklogGroup, on_delete=models.PROTECT, related_name='container', null=True)
    
    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.backlogs.delete()
        super().delete(*args, **kwargs)


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
    emote = models.ForeignKey(Emote, on_delete=models.CASCADE, null=True)
    chatter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reactions', null=True)
    group = models.ForeignKey(ReactionGroup, on_delete=models.CASCADE, related_name='items', null=True)


# *Action
class Action(models.Model):
    name = models.CharField(max_length=20)
    display_name = models.CharField(max_length=20)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f'{self.name}: {self.description}'
    

# *Backlog
class Backlog(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.reactions = ReactionGroup.objects.create()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.reactions.delete()
        super().delete(*args, **kwargs)

    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")

# *Message
class Message(Backlog):
    group = models.ForeignKey(BacklogGroup, on_delete=models.CASCADE, related_name='messages', null=True)
    reactions = models.OneToOneField(ReactionGroup, on_delete=models.CASCADE, related_name='message', null=True)

    content = models.CharField(max_length=1000, blank=False)
    user = models.ForeignKey(CustomUser, related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.pk} | user: {self.user} (pk: {self.user.pk}) | room: {self.channel.room.name} | channel: {self.channel.name}'


# *Log
class Log(Backlog):
    group = models.ForeignKey(BacklogGroup, on_delete=models.CASCADE, related_name='logs', null=True)
    reactions = models.OneToOneField(ReactionGroup, on_delete=models.CASCADE, related_name='log', null=True)

    action = models.ForeignKey(Action, related_name='logs', on_delete=models.SET_NULL, null=True)
    receiver = models.ForeignKey(CustomUser, related_name='received_actions', on_delete=models.SET_NULL, null=True)
    sender = models.ForeignKey(CustomUser, related_name='sent_actions', on_delete=models.SET_NULL, null=True, blank=True)



# *ChannelCategory
class ChannelCategory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='categories', null=True)
    name = models.CharField(max_length=30)
    order = models.PositiveIntegerField(default=20, validators=[MaxValueValidator(20), MinValueValidator(1)])
    
    def __str__(self):
        return f'{self.room}: {self.name} | order: {self.order}'


# *Channel
class Channel(BacklogContainer):
    TEXT = 'text'
    VOICE = 'voice'
    KIND = (
        (TEXT, 'Text Channel'),
        (VOICE, 'Voice Channel'),
    )
    name = models.CharField(max_length=30, blank=False)
    description = models.CharField(max_length=60, blank=True)
    category = models.ForeignKey(ChannelCategory, on_delete=models.SET_NULL, related_name='channels', null=True, blank=True)
    kind = models.CharField(max_length=20, choices=KIND, default=TEXT)
    order = models.PositiveIntegerField(default=20, validators=[MaxValueValidator(20), MinValueValidator(1)])
    backlogs = models.OneToOneField(BacklogGroup, on_delete=models.CASCADE, related_name='channel')
    group = models.ForeignKey(ChannelGroup, on_delete=models.PROTECT, related_name='channels', null=True)
            
    def __str__(self):
        return f'{self.room}: {self.name}'
    

# *PriveChat
class PrivateChat(BacklogContainer):
    chatters = models.OneToOneField(ChatterGroup, on_delete=models.PROTECT, related_name='private_chat', null=True)
    
    
# *ChannelConfiguration
class ChannelConfiguration(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='channels_configs', null=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='configs', null=True)

    def __str__(self):
        return f'channel {self.channel.pk} & role {self.role.pk}'


# *ChannelConfigurationPermissions
class ChannelConfigurationPermissions(models.Model):
    config = models.ForeignKey(ChannelConfiguration, on_delete=models.CASCADE, related_name='permissions', null=True)
    CHOICES = (
        ('True', 'True'),
        ('False', 'False'),
        ('Null', 'Null')
    )
    add_message = models.CharField(max_length=10, choices=CHOICES, default='Null')
    view_message = models.CharField(max_length=10, choices=CHOICES, default='Null')
    view_channel = models.CharField(max_length=10, choices=CHOICES, default='Null')
    add_reaction = models.CharField(max_length=10, choices=CHOICES, default='Null')
    attach_image = models.CharField(max_length=10, choices=CHOICES, default='Null')
    manage_role = models.CharField(max_length=10, choices=CHOICES, default='Null')
    

