import datetime
import random

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db.models import Q
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("Email Required"))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

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
    username = models.CharField(max_length=30, null=True)

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

    def __str__(self):
        return f'{self.username}#{str(self.username_id).zfill(2)}'
    
    def friendships(self):
        return Friendship.objects.filter(Q(sender=self) | Q(receiver=self))

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
    



class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    username_id = models.PositiveIntegerField(null=True)
    username = models.CharField(max_length=30, null=True)

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
        (ONLINE, 'On-line'),
        (OFFLINE, 'Off-line'),
    )
    status = models.CharField(max_length=10, choices=STATUS, default=ONLINE)

    def friendships(self):
        return Friendship.objects.filter(Q(sender=self.user) | Q(receiver=self.user))

    def __str__(self):
        return self.user.username
    

class FriendshipQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status='pending')
    
    def accepted(self):
        return self.filter(status='accepted')
    

class Friendship(models.Model):
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted')])
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='outgoing_friend_requests')
    receiver = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='incoming_friend_requests')
    
    def users(self):
        return {self.sender, self.receiver}
    
    objects = FriendshipQuerySet.as_manager()

