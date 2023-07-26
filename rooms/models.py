from itertools import chain
from datetime import datetime

from django.db import models
from django.db.models import Q, F
from django.contrib.auth.models import Permission
from django.core.validators import MaxValueValidator, MinValueValidator

from users.models import CustomUser


class Chat(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class GroupChat(Chat):
    owner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='groups_owned', null=True)
    name = models.CharField(max_length=50)
    image = models.ImageField(max_length=500, blank=True)
    public = models.BooleanField(default=False)
    base_role = models.OneToOneField('Role', on_delete=models.RESTRICT, related_name='+', null=True, blank=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            super().save(*args, **kwargs)
            default_category = Category.objects.create(name='Text Channels', chat=self)
            default_channel = GroupChannel.objects.create(name='General', chat=self, category=default_category)
            
            self.base_role = Role.objects.create(name='all', chat=self)
            owner_membership = GroupChatMembership.objects.create(user=self.owner, chat=self)
            self.base_role.memberships.add(owner_membership)

        super().save(*args, **kwargs)

    def channels_and_categories(self):
        return chain(self.categories.all(), self.channels.all().filter(category=None))


class PrivateChat(Chat):
    pass


class Membership(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class GroupChatMembership(Membership):
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_chat_memberships')

    nickname = models.CharField(max_length=20, blank=True)


class PrivateChatMembership(Membership):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='private_chat_memberships')


class Category(models.Model):
    name = models.CharField(max_length=20)
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='categories')


class Channel(models.Model):    
    date_created = models.DateTimeField(auto_now_add=True)
    pinned_messages = models.ManyToManyField('Message', blank=True)

    class Meta:
        abstract = True


class PrivateChannel(Channel):
    chat = models.OneToOneField(PrivateChat, on_delete=models.CASCADE, related_name='channel', null=True)
    
    def save(self, *args, **kwargs):
        creating = self._state.adding
        
        if creating:
            super().save(*args, **kwargs)
            BacklogGroup.objects.create(kind='private_channel', private_channel=self)

        super().save(*args, **kwargs)


class GroupChannel(Channel):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=1024, blank=True)
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='channels', null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='channels', null=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            super().save(*args, **kwargs)
            BacklogGroup.objects.create(kind='group_channel', group_channel=self)
        else:
            super().save(*args, **kwargs)


class BacklogGroup(models.Model):
    KINDS = (
        ('group_channel', 'Group Chat Backlogs'),
        ('private_channel', 'Private Chat Backlogs'),
    )

    kind = models.CharField(max_length=20, choices=KINDS)
    group_channel = models.OneToOneField(GroupChannel, on_delete=models.CASCADE, related_name='backlog_group', null=True)
    private_channel = models.OneToOneField(PrivateChannel, on_delete=models.CASCADE, related_name='backlog_group', null=True)

    def get_chat(self):
        return getattr(self, self.kind)


class Backlog(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    
    KINDS = (
        ('message', 'Message'),
        ('log', 'Log')
    )

    kind = models.CharField(max_length=20, choices=KINDS)
    date_created = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(BacklogGroup, on_delete=models.CASCADE, related_name='backlogs', null=True)

    def timestamp(self):
        return self.date_created.strftime("%H:%M:%S")


class Message(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='messages', null=True)
    backlog = models.OneToOneField(Backlog, on_delete=models.CASCADE, related_name='message')
    content = models.CharField(max_length=1024)


class Log(models.Model):
    ACTIONS = (
        ('join', 'joined the chat'),
        ('leave', 'left the chat'),
    )

    action = models.CharField(max_length=20, choices=ACTIONS)
    receiver = models.ForeignKey(CustomUser, related_name='received_actions', on_delete=models.SET_NULL, null=True)
    sender = models.ForeignKey(CustomUser, related_name='sent_actions', on_delete=models.SET_NULL, null=True, blank=True)
    backlog = models.OneToOneField(Backlog, on_delete=models.CASCADE, related_name='log')


class Role(models.Model):
    name = models.CharField(max_length=20)
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='roles')
    memberships = models.ManyToManyField(GroupChatMembership, related_name='roles')


"""
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
    group = models.ForeignKey(ReactionGroup, on_delete=models.CASCADE, related_name='reactions', null=True)



    

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
    content = models.CharField(max_length=1000, blank=False)
    group = models.ForeignKey(BacklogGroup, on_delete=models.CASCADE, related_name='messages', null=True)
    reactions = models.OneToOneField(ReactionGroup, on_delete=models.CASCADE, related_name='message', null=True)
    user = models.ForeignKey(CustomUser, related_name='messages', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.pk} | user: {self.user} (pk: {self.user.pk}) | room: {self.channel.room.name} | channel: {self.channel.name}'





# *ChannelCategory
class ChannelCategory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='categories', null=True)
    name = models.CharField(max_length=30)
    order = models.PositiveIntegerField(default=20, validators=[MaxValueValidator(20), MinValueValidator(1)])
    
    def __str__(self):
        return f'{self.room}: {self.name} | order: {self.order}'


# *BacklogContainer
class BacklogContainer(models.Model):
    backlogs = models.OneToOneField(BacklogGroup, on_delete=models.PROTECT, related_name='container', null=True)
    
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.backlogs = BacklogGroup.objects.create()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.backlogs.delete()
        super().delete(*args, **kwargs)


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
    backlogs = models.OneToOneField(BacklogGroup, on_delete=models.PROTECT, related_name='channel', null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='channels', null=True)

    def __str__(self):
        return f'{self.room}: {self.name}'
    


    

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

"""