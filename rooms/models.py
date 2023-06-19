from PIL import Image
from itertools import chain
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError

from users.models import CustomUser


# *Room
class Room(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True)
    owner = models.ForeignKey(CustomUser, related_name='servers_owned', null=True, on_delete=models.SET_NULL)
    image = models.ImageField(default='blank.png', max_length=500)
    date_added = models.DateTimeField(auto_now_add=True)
    default_role = models.OneToOneField('Role', on_delete=models.CASCADE, related_name='+', null=True)
    public = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ('kick_user', 'Can kick user'),
            ('ban_user', 'Can ban user'),
            ('read_logs', 'Can read logs'),
        ]

    def save(self, *args, **kwargs):
        created = getattr(self, 'pk', None) is None
        super().save(*args, **kwargs)
        if created:
            default_category = ChannelCategory.objects.create(
                room=self,
                name='Text Channels',
                order=0,
            )


            default_role = Role.objects.create(room=self, name='all', color='#e0dbd1')
            self.default_role = default_role


            default_channel = Channel.objects.create(
                room=self,
                name='general',
                description='default channel', 
                category=default_category
            )
            default_channel.display_logs.set(Action.objects.all())


            owner_member = Member.objects.create(user=self.owner, room=self)
            owner_member.roles.add(default_role)

            super().save(*args, **kwargs)
    
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

    def save(self, *args, **kwargs):
        created = getattr(self, 'pk', None) is None
        super().save(*args, **kwargs)
        if created:
            config = ChannelConfiguration.objects.create(
                role = self.room.default_role,
                channel = self
            )
            
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
    admin = models.BooleanField(default=False)
    permissions = models.OneToOneField('ModelPermissionGroup', on_delete=models.CASCADE, related_name='role', null=True)
    
    class Meta:
        permissions = [
            ('manage_role', 'Can manage role'),
            ('mention_all', 'Can mention @all')
        ]

    def save(self, *args, **kwargs):
        created = getattr(self, 'pk', None) is None
        super().save(*args, **kwargs)
        if created:
            self.set_default_perms()
    
    def delete(self, *args, **kwargs):
        cascade = kwargs.get('cascade', False)
        if self != self.room.default_role:
            self.permissions.delete(cascade=cascade)
            super().delete(*args, **kwargs)
            return

        if cascade:
            self.permissions.delete(cascade=cascade)
            super().delete(*args, **kwargs)
        else:
            raise ValueError('Cannot delete default role without deleting Room')

    def set_default_perms(self):
        # Only the first role requires explicit perms
        if self.room.default_role:
            default_permissions = {
                'add_message': None, 
                'delete_message': None,
                'view_message': None, 
                'view_channel': None, 
                'add_reaction': None, 
                'attach_image': None, 
                'change_nickname': None,
                'manage_nickname': None,
                'manage_channel': None,
                'manage_role': None,
                'change_room': None,
                'mention_all': None,
                'pin_message': None,
                'kick_user': None, 
                'ban_user': None,
                'read_logs': None,
            }
        else:
             default_permissions = {
                'add_message': True, 
                'delete_message': True,
                'view_message': True, 
                'view_channel': True, 
                'add_reaction': True, 
                'attach_image': True, 
                'change_nickname': True,
                'manage_nickname': False,
                'manage_channel': False,
                'manage_role': False,
                'change_room': False,
                'mention_all': True,
                'pin_message': False,
                'kick_user': False, 
                'ban_user': False,
                'read_logs': False,
            }

        self.permissions = ModelPermissionGroup.objects.create()
        for codename, value in default_permissions.items():
            ModelPermission.objects.create(
                permission=Permission.objects.get(codename=codename),
                group=self.permissions,
                value=value,
            )

        self.save()   

    def __str__(self):
        return f'role: {self.pk}'


class MemberQuerySet(models.QuerySet):
    def online(self):
        return self.filter(user__status='online')
    
    def offline(self):
        return self.filter(user__status='offline')
    

# *Member
class Member(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, related_name='memberships')
    roles = models.ManyToManyField(Role, related_name='members')
    room = models.ForeignKey(Room, related_name='members', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=30, blank=True)

    objects = MemberQuerySet.as_manager()

    class Meta:
        permissions = [
            ('change_nickname', 'Can change nickname'),
            ('manage_nickname', 'Can manage nickname')
        ]
    

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

    def __str__(self):
            return f'{self.room.pk}: {self.user.__str__()}' +f'{self.nickname or ""}'


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
        
        permissions = [
            ('pin_message', 'Can pin message'),
            ('attach_image', 'Can attach image')
        ]
    
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
    
# *ChannelConfig
class ChannelConfiguration(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='channels_configs')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='configs')
    permissions = models.OneToOneField('ModelPermissionGroup', on_delete=models.CASCADE, related_name='channel_configuration', null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'channel'], 
                name='Channel Config'
            )
        ]
        permissions = [
            ('manage_channel', 'Can manage channel'),
        ]

    def save(self, *args, **kwargs):
        created = getattr(self, 'pk', None) is None
        super().save(*args, **kwargs)
        if created:
            self.set_default_perms()

    def set_default_perms(self):
        default_permissions = {
            'add_message': None,
            'view_message': None,
            'view_channel': None,
            'add_reaction': None,
            'attach_image': None,
            'manage_role': None,
        }
        self.permissions = ModelPermissionGroup.objects.create()
        for codename, value in default_permissions.items():
            ModelPermission.objects.create(
                permission=Permission.objects.get(codename=codename),
                group=self.permissions,
                value=value,
            )

        self.save()
    
    def __str__(self):
        return f'channel {self.channel.pk} & role {self.role.pk}'


# *ModelPermission
class ModelPermission(models.Model):
    CHOICES = (
        (True, 'True'),
        (False, 'False'),
        (None, 'None')
    )
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    group = models.ForeignKey('ModelPermissionGroup', on_delete=models.CASCADE, related_name='items')
    value = models.CharField(max_length=20, choices=CHOICES, null=True, blank=True)

    def __str__(self):
        return f'{self.group.__str__()} |*| {self.permission.codename}: {self.value}'

# *ModelPermissionGroup
class ModelPermissionGroup(models.Model):
    def __str__(self):
        if hasattr(self, 'role'):
            return self.role.__str__()
        elif hasattr(self, 'channel_configuration'):
            return self.channel_configuration.__str__()