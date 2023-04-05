import datetime

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.sessions.models import Session

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='blank.png')
    bio = models.TextField(max_length=50, blank=True)
    birthday = models.DateField(blank=False, null=True)
    last_ping = models.DateTimeField()
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


    def __str__(self):
        return self.user.username



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()