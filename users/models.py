from datetime import datetime, timezone

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from core.models import Archive


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("Email Required"))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        existing_username_ids = CustomUser.objects.filter(
            username=user.username
        ).values_list('username_id', flat=True)
        free_ids = [value for value in range(0, 100) if value not in existing_username_ids]
        if not free_ids:
            raise ValueError(_("All ID's for this username are already taken"))
        user.username_id = free_ids.pop(0)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("birthday", datetime.now(timezone.utc))

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    username_id = models.PositiveIntegerField(null=True)
    username = models.CharField(max_length=30, default='user')
    image = models.ImageField(default='blank.png')
    
    bio = models.TextField(max_length=50, blank=True)
    birthday = models.DateField(blank=False, null=True)
    last_ping = models.DateTimeField(auto_now_add=True)
    
    twitter = models.CharField(max_length=500, blank=True)
    steam = models.CharField(max_length=500, blank=True)
    twitch = models.CharField(max_length=500, blank=True)
    spotify = models.CharField(max_length=500, blank=True)
    
    premium = models.BooleanField(default=False, blank=True)

    ONLINE = 'online'
    OFFLINE = 'offline'
    STATUS = (
        (ONLINE, 'Online'),
        (OFFLINE, 'Offline'),
    )
    status = models.CharField(max_length=10, choices=STATUS, default=OFFLINE)


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)

        if creating:
            archive = Archive.objects.create(data={
                'model': 'CustomUser',
                'pk': self.pk,
                'username': self.username,
                'username_id': self.username_id,
                'birthday': self.birthday.isoformat(),
                'date_joined': self.date_joined.isoformat(),
            })
                        
            UserArchive.objects.create(user=self, archive=archive)

    def get_friendships(self):
        return Friendship.objects.filter(Q(sender=self) | Q(receiver=self))
    
    def get_private_chats(self):
        PrivateChat = apps.get_model('rooms', 'PrivateChat')
        return PrivateChat.objects.filter(memberships__user=self)

    def friends(self):
        return map(lambda obj: obj.other_party(), self.friend_objects.all())

    def joined(self):
        return self.date_joined.strftime("%d %B %Y")
    
    def full_name(self):
        return f'{self.username}#{self.formatted_username_id()}'
    
    def formatted_username_id(self):
        return str(self.username_id).zfill(2)
    
    def get_group_chat_memberships(self):
        return self.group_chat_memberships.all().select_related('chat')
    
    def generate_notifications(self):
        notifications_by_id = {'initial': {'unread_backlogs': 0}}
        private_chat_trackers = self.backlog_trackers.filter(backlog_group__kind='private_chat')

        for tracker in private_chat_trackers:
            unread_backlog_count = tracker.get_unread_backlogs().count()
            notifications_by_id[f'backlog-group-{tracker.backlog_group.pk}-unreads'] = unread_backlog_count
            notifications_by_id['initial']['unread_backlogs'] += unread_backlog_count
       
        for friendship in self.get_friendships().pending():
            notifications_by_id[f'friendship-{friendship.pk}'] = 1
            notifications_by_id['initial']['unread_backlogs'] += 1

        return notifications_by_id

    def __str__(self):
        return f'{self.username}#{self.formatted_username_id()}'
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(username_id__gte=0) & Q(username_id__lte=99),
                name='Valid username ID'
            ),
            models.UniqueConstraint(
                fields=['username', 'username_id'],
                name='Verify unique username ID'
            )
        ]


class UserArchive(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, related_name='user_archive')
    archive = models.OneToOneField(Archive, on_delete=models.PROTECT)

    def __getattr__(self, attr):
        if self.user and hasattr(self.user, attr):
            return getattr(self.user, attr)
        elif self.archive.data.get(attr):
            return self.archive.data.get(attr)
        else:
            raise AttributeError(f"'UserArchive' object has no attribute '{attr}'")

    def __str__(self):
        if self.user:
            return self.user.__str__()
        else:
            return f'user-{self.pk}'


class FriendshipQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status='pending')
    
    def accepted(self):
        return self.filter(status='accepted')
    

class Friendship(models.Model):
    CHOICES = (
        ('accepted', 'Friends'),
        ('pending', 'Pending Friendship'),
    )

    status = models.CharField(max_length=20, choices=CHOICES)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_friendships')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_friendships')
    objects = FriendshipQuerySet.as_manager()

    def sender_profile(self):
        return self.members.get(user=self.sender)
    
    def receiver_profile(self):
        return self.members.get(user=self.receiver)


class Friend(models.Model):
    friendship = models.ForeignKey(Friendship, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='friend_objects', null=True)
    nickname = models.CharField(max_length=30, blank=True)

    def other_party(self):
        return self.friendship.members.all().exclude(user=self.user).first()