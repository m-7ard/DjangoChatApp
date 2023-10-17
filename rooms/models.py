import re
import html
import json
from itertools import chain
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sorl.thumbnail import ImageField, get_thumbnail

from django.db import models
from django.core.validators import RegexValidator
from channels.layers import get_channel_layer
from django.template.loader import render_to_string

from users.models import CustomUser, UserArchive
from utils import get_object_or_none

channel_layer = get_channel_layer()


class Chat(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)

    def get_member(self, pk):
        return self.memberships.filter(user__pk=pk).first()

    class Meta:
        abstract = True


class GroupChat(Chat):
    owner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='groups_owned', null=True)
    name = models.CharField(max_length=50)
    image = models.ImageField(max_length=500, blank=True, default='1213.png')
    public = models.BooleanField(default=False)
    base_role = models.OneToOneField('Role', on_delete=models.RESTRICT, related_name='+', null=True, blank=True)
    role_order = models.JSONField(default=list)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            super().save(*args, **kwargs)
            self.base_role = Role.objects.create(name='all', chat=self)
            owner_membership = GroupChatMembership.objects.create(user=self.owner, chat=self)
            
            default_category = Category.objects.create(name='Text Channels', chat=self)
            default_channel = GroupChannel.objects.create(name='General', chat=self, category=default_category)
            self.base_role.can_see_channels.add(default_channel)
            self.base_role.can_use_channels.add(default_channel)

        super().save(*args, **kwargs)

    def channels_and_categories(self):
        return chain(self.categories.all(), self.channels.all().filter(category=None))

    def get_roles(self):
        return self.roles.all()

class BacklogGroupWrapper(models.Model):
    def get_chat(self):
        return getattr(self, 'chat', self)
    
    class Meta:
        abstract = True


class PrivateChat(Chat, BacklogGroupWrapper):
    pinned_messages = models.ManyToManyField('Message', blank=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            super().save(*args, **kwargs)
            BacklogGroup.objects.create(kind='private_chat', private_chat=self)
        else:
            super().save(*args, **kwargs)

    def user_list(self):
        return [membership.user for membership in self.memberships.all()]


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
            
            self.chat.base_role.members.add(self)
        else:
            super().save(*args, **kwargs)

    def roles_by_importance(self):
        return sorted(
            self.roles.all(), 
            key=lambda role: role.get_order()
        )

    def display_color(self):
        roles_by_importance = self.roles_by_importance()
        return roles_by_importance[0].color
    
    def is_owner(self):
        return self.user == self.chat.owner

    def visible_channels(self):
        if self.is_owner():
            return self.chat.channels.values_list('pk', flat=True)
        
        return self.roles.values_list('can_see_channels', flat=True)

    def has_perm(self, perm_name):
        roles_by_importance = self.roles_by_importance()

        if self.is_owner():
            return True
        
        for role in roles_by_importance:
            if role.admin:
                return True

        for role in roles_by_importance:
            perm_value = role.get_perm_value(perm_name)
            if perm_value is not None:
                return perm_value

    def display_name(self):
        if self.user.is_null():
            return self.user.username

        return self.nickname or self.user.username
    
    def joined(self):
        return self.date_created.strftime("%d %B %Y")

    def delete(self, *args, **kwargs):
        channels = self.chat.channels.all()
        backlog_group_pks = channels.values_list('backlog_group')
        trackers = BacklogGroupTracker.objects.filter(user=self.user, backlog_group__pk__in=backlog_group_pks)
        trackers.delete()
        super().delete(*args, **kwargs)

    def get_roles(self):
        return self.roles.all()


class PrivateChatMembership(Membership):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='private_chat_memberships')
    active = models.BooleanField(default=False)

    def display_color(self):
        return None
    
    def display_name(self):
        return self.user.username

    def other_party(self):
        return self.chat.memberships.all().exclude(user=self.user).first()
    
    @classmethod
    def has_perm(cls, perm_name):
        return perm_name in [
            'can_create_messages',
            'can_react',
        ]
    
    def activate(self):
        previous_state = self.active
        self.active = True
        self.save()
        return previous_state == False
    
    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            BacklogGroupTracker.objects.create(user=self.user, backlog_group=self.chat.backlog_group)

        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=20)
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='categories')


class GroupChannel(BacklogGroupWrapper):
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
            
            self.chat.base_role.can_see_channels.add(self)
            self.chat.base_role.can_use_channels.add(self)
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

    def get_chat(self):
        return self.group.belongs_to().get_chat()

    KINDS = (
        ('message', 'Message'),
        ('log', 'Log')
    )

    kind = models.CharField(max_length=20, choices=KINDS)
    date_created = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(BacklogGroup, on_delete=models.CASCADE, related_name='backlogs', null=True)
    user_mentions = models.ManyToManyField(CustomUser, related_name='mentioned_in')
    role_mentions = models.ManyToManyField('Role', related_name='mentioned_in')

    def timestamp(self):
        return self.date_created.strftime("%H:%M:%S")
    
    def __str__(self):
        return f'({self.pk}) | {self.kind}'
    

class Message(models.Model):
    user_archive = models.ForeignKey(UserArchive, on_delete=models.PROTECT, related_name='messages', null=True)
    backlog = models.OneToOneField(Backlog, on_delete=models.CASCADE, related_name='message')
    content = models.CharField(max_length=1024)
    rendered_content = models.CharField(max_length=5000)
    invites = models.JSONField(default=list)
    attachment = models.ImageField(blank=True)

    def get_member(self):
        chat = self.backlog.get_chat()
        return chat.get_member(self.user.pk)

    def get_attributes(self):
        member = self.get_member()
        if member:
            return {
                'display_name': member.display_name(),
                'display_color': member.display_color(),
                'image': member.user.image,
                'profile_kwargs': json.dumps({'group_chat_membership_pk': self.pk})
            }
        
    def get_user_mentions(self):
        return re.findall(r'(?<!\w)>>(\w+#\d{2})(?!\w)', self.content)
    
    def get_role_mentions(self):
        return re.findall(r'(?<!\w)>>(\w+)(?!\w)', self.content)

    def get_invites(self):
        return re.findall(r'(?<!\w)DjangoChatApp/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?!\w)', self.content)

    def process_content(self, users, roles):
        processed_content = html.escape(self.content)

        for user in users:
            processed_content = re.sub(
                rf'(?<!\w){html.escape(">>" + user.full_name())}(?!\w)', 
                lambda match: render_to_string('rooms/elements/mentions/user-mention.html', {'backlog': self.backlog, 'user': user}), 
                processed_content
            )

        for role in roles:
            processed_content = re.sub(
                rf'(?<!\w){html.escape(">>" + role.name)}(?!\w)', 
                lambda match: render_to_string('rooms/elements/mentions/role-mention.html', {'role': role}), 
                self.content
            )
        
        return processed_content


    def process_invites(self):
        invites = []

        for invite_directory in self.invites:
            invite = get_object_or_none(Invite, directory=invite_directory)
            if not invite:
                invites.append({
                    'directory': invite_directory,
                    'valid': False
                })
            else:
                invites.append({
                    'directory': invite_directory,
                    'valid': True,
                    'is_expired': invite.is_expired(),
                    'chat': {
                        'pk': invite.get_chat().pk,
                        'name': invite.get_chat().name,
                        'image': {'url': invite.get_chat().image.url},
                        'memberships': list(invite.get_chat().memberships.values_list('user', flat=True))
                    }
                })

        return sorted(invites, key=lambda invite: self.content.find(invite['directory']))[-10:]

    def save(self, *args, **kwargs):
        users = set()
        for full_name in self.get_user_mentions():
            username, username_id = full_name.split('#')
            user = get_object_or_none(CustomUser, username=username, username_id=username_id)
            if user:
                users.add(user)
        
        roles = set()
        if self.backlog.group.kind == 'group_channel':
            chat = self.backlog.group.group_channel.chat
            for role_name in self.get_role_mentions():
                role = chat.roles.filter(name=role_name).first()
                if role:
                    roles.add(role)
        
        
        self.backlog.user_mentions.set(users)
        self.backlog.role_mentions.set(roles)
        self.rendered_content = self.process_content(users, roles)
        self.invites = [invite.split('/')[-1] for invite in set(self.get_invites())]
        super().save(*args, **kwargs)


class Log(models.Model):
    ACTIONS = (
        ('join', 'Join Chat'),
        ('leave', 'Leave Chat'),
    )
    
    ACTION_TYPE = {
        'join': '1 user action',
        'leave': '1 user action',
    }

    ACTION_STRING = {
        'join': 'joined the chat',
        'leave': 'left the chat',
    }

    action = models.CharField(max_length=20, choices=ACTIONS)
    user1_archive = models.ForeignKey(UserArchive, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)
    user2_archive = models.ForeignKey(UserArchive, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)
    backlog = models.OneToOneField(Backlog, on_delete=models.CASCADE, related_name='log')

    def get_action_type(self):
        return self.ACTION_TYPE[self.action]
    
    def get_action_string(self):
        return self.ACTION_STRING[self.action]

    def save(self, *args, **kwargs):
        creating = self._state.adding

        if creating:
            self.backlog.user_mentions.set([self.user1, self.user2])

        super().save(*args, **kwargs)


class Role(models.Model):
    CHOICES = (
        (1, True),
        (0, None),
        (-1, False),
    )

    name = models.CharField(max_length=20)
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='roles')
    members = models.ManyToManyField(GroupChatMembership, related_name='roles')
    color = models.CharField(max_length=7, default='#DBD6CC', validators=[RegexValidator(
            regex=r'#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?$',
            message='Please enter a valid hex color code.',
            code='invalid_chars'
        ),
    ])
    can_see_channels = models.ManyToManyField(GroupChannel, related_name='can_see_channel')
    can_use_channels = models.ManyToManyField(GroupChannel, related_name='can_use_channel')
    # can_see_category ...
    # can_use_category ...
    can_create_messages = models.IntegerField(default=1, choices=CHOICES)
    can_manage_messages = models.IntegerField(default=-1, choices=CHOICES)
    can_react = models.IntegerField(default=1, choices=CHOICES)
    can_manage_channels = models.IntegerField(default=-1, choices=CHOICES)
    can_manage_chat = models.IntegerField(default=-1, choices=CHOICES)
    can_mention_all = models.IntegerField(default=1, choices=CHOICES)
    can_kick_members = models.IntegerField(default=-1, choices=CHOICES)
    can_ban_members = models.IntegerField(default=-1, choices=CHOICES)
    can_create_invites = models.IntegerField(default=1, choices=CHOICES)
    can_get_invites = models.IntegerField(default=1, choices=CHOICES)
    can_manage_invites = models.IntegerField(default=-1, choices=CHOICES)
    can_manage_emotes = models.IntegerField(default=-1, choices=CHOICES)
    can_manage_roles = models.IntegerField(default=-1, choices=CHOICES)

    # gives user all permissions
    admin = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        if self.pk in self.chat.role_order:
            self.chat.role_order.remove(self.pk)

        super().delete(*args, **kwargs)

    def get_perm_value(self, perm_name):
        raw_value = getattr(self, perm_name)
        if raw_value == -1:
            return False
        elif raw_value == 0:
            return None
        elif raw_value == 1:
            return True
        
    def get_order(self):
        if self == self.chat.base_role:
            return float('inf')
        
        if self.pk in self.chat.role_order:
            return self.chat.role_order.index(self.pk)
        
        return self.pk + 10000

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'chat'], name='unique_role_name')
        ]


def invite_default_expiry_date():
    return datetime.now(timezone.utc) + timedelta(days=1)


class Invite(models.Model):
    CHOICES = (
        ('1 day', '1 Day'),
        ('7 days', '7 Days'),
        ('30 days', '30 Days'),
        ('365 days', '365 Days'),
        ('forever', 'Forever')
    )

    KINDS = (
        ('group_chat', 'Group Chat Invite'),
    )

    kind = models.CharField(max_length=20)
    group_chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='invites', null=True, blank=True)
    directory = models.UUIDField(default=uuid4, editable=False)
    one_time = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(default=invite_default_expiry_date)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='+', null=True)

    def full_link(self):
        return f'DjangoChatApp/{self.directory}'

    def is_expired(self):
        return self.expiry_date < datetime.now(timezone.utc)
    
    def __str__(self):
        return f'Expired: {self.is_expired()} | {str(self.directory)}'
    
    def get_chat(self):
        return getattr(self, self.kind)


class BacklogGroupTracker(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='backlog_trackers')
    backlog_group = models.ForeignKey(BacklogGroup, on_delete=models.CASCADE, related_name='+')
    last_backlog_seen = models.ForeignKey(Backlog, on_delete=models.SET_NULL, related_name='+', null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def unread_backlogs(self):
        last_backlog_seen = self.last_backlog_seen

        if last_backlog_seen:
            new_backlogs = self.backlog_group.backlogs.filter(date_created__gt=last_backlog_seen.date_created)
        else:
            new_backlogs = self.backlog_group.backlogs.all()
        
        return new_backlogs

    def __str__(self):
        return f'{self.backlog_group.kind} ({self.backlog_group.belongs_to().pk}) {self.user.full_name()} ({self.user.pk})'


class Emote(models.Model):
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='emotes')
    name = models.CharField(max_length=20, validators=[RegexValidator(
            regex=r'^[a-zA-Z0-9_-]+$',
            message='Only alphanumeric characters, hyphens, and underscores are allowed.',
            code='invalid_chars'
        ),
    ])
    image = ImageField()
    user_archive = models.ForeignKey(UserArchive, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding
        
        if self.image and creating:
            super().save(*args, **kwargs)
            self.image = get_thumbnail(self.image, '128x128', quality=99, format='PNG').url

        super().save(*args, **kwargs)

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'chat'], name='unique_emote_name')
        ]


class Emoji(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50)
    image = models.ImageField()
    emoji_literal = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.emoji_literal}: {self.name}'


class Reaction(models.Model):
    kind = models.CharField(max_length=20, choices=(
        ('emoji', 'emoji'),
        ('emote', 'emote'),
    ))
    backlog = models.ForeignKey(Backlog, on_delete=models.CASCADE, related_name='reactions')
    user_archives = models.ManyToManyField(UserArchive)
    emote = models.ForeignKey(Emote, on_delete=models.CASCADE, related_name='+', null=True)
    emoji = models.ForeignKey(Emoji, on_delete=models.CASCADE, related_name='+', null=True)

    def get_emoticon(self):
        return getattr(self, self.kind)