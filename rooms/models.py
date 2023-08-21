from itertools import chain
from datetime import datetime, timedelta, timezone
from uuid import uuid4

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
            self.base_role = Role.objects.create(name='all', chat=self)
            owner_membership = GroupChatMembership.objects.create(user=self.owner, chat=self)
            self.base_role.memberships.add(owner_membership)
            
            default_category = Category.objects.create(name='Text Channels', chat=self)
            default_channel = GroupChannel.objects.create(name='General', chat=self, category=default_category)

        super().save(*args, **kwargs)

    def channels_and_categories(self):
        return chain(self.categories.all(), self.channels.all().filter(category=None))


class PrivateChat(Chat):
    pinned_messages = models.ManyToManyField('Message', blank=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            super().save(*args, **kwargs)
            BacklogGroup.objects.create(kind='private_chat', private_chat=self)
        else:
            super().save(*args, **kwargs)

class Membership(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class GroupChatMembership(Membership):
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_chat_memberships')
    nickname = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            super().save(*args, **kwargs)
            for channel in self.chat.channels.all():
                BacklogGroupTracker.objects.create(user=self.user, backlog_group=channel.backlog_group)
        else:
            super().save(*args, **kwargs)

class PrivateChatMembership(Membership):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='private_chat_memberships')
    active = models.BooleanField(default=False)

    def other_party(self):
        return self.chat.memberships.all().exclude(user=self.user).first()
    
    def activate(self):
        previous_state = self.active
        self.active = True
        self.save()
        return previous_state == False
    

class Category(models.Model):
    name = models.CharField(max_length=20)
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='categories')


class GroupChannel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    pinned_messages = models.ManyToManyField('Message', blank=True)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=1024, blank=True)
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='channels', null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='channels', null=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            super().save(*args, **kwargs)
            BacklogGroup.objects.create(kind='group_channel', group_channel=self)
            for membership in self.chat.memberships.all():
                BacklogGroupTracker.objects.create(user=membership.user, backlog_group=self.backlog_group)
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.chat.name} ({self.chat.pk}) >>> {self.name} ({self.pk})'


class BacklogGroup(models.Model):
    KINDS = (
        ('group_channel', 'Group Chat Backlogs'),
        ('private_chat', 'Private Chat Backlogs'),
    )

    kind = models.CharField(max_length=20, choices=KINDS)
    group_channel = models.OneToOneField(GroupChannel, on_delete=models.CASCADE, related_name='backlog_group', null=True)
    private_chat = models.OneToOneField(PrivateChat, on_delete=models.CASCADE, related_name='backlog_group', null=True)

    def belongs_to(self):
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
    
    def __str__(self):
        return f'({self.pk}) | {self.kind}'
    

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


def invite_default_expiry_date():
    return datetime.now(timezone.utc) + timedelta(days=1)


class Invite(models.Model):
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='invites')
    directory = models.UUIDField(default=uuid4, editable=False)
    one_time = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(default=invite_default_expiry_date)

    def is_valid(self):
        return self.expiry_date > datetime.now(timezone.utc)
    
    def __str__(self):
        return f'{self.is_valid()} - {str(self.directory)}'


class BacklogGroupTracker(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='backlog_trackers')
    backlog_group = models.ForeignKey(BacklogGroup, on_delete=models.CASCADE, related_name='+')
    last_backlog_seen = models.ForeignKey(Backlog, on_delete=models.CASCADE, related_name='+', null=True)
    
    def unread_backlogs(self):
        if not self.last_backlog_seen:
                return self.backlog_group.backlogs.all()
        
        return self.backlog_group.backlogs.filter(date_created__gt=self.last_backlog_seen.date_created)

    def update(self):
        latest = self.backlog_group.backlogs.last()
        changing = self.last_backlog_seen != latest
        if changing:
            self.last_backlog_seen = latest
            self.save()
        
        return changing

    def __str__(self):
        return f'{self.backlog_group.kind} ({self.backlog_group.belongs_to().pk}) {self.user.full_name()} ({self.user.pk})'

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