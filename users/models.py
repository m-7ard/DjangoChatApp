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
    profile_picture = models.ImageField(default='unknown.jpg')
    twitter = models.CharField(max_length=500, blank=True)
    steam = models.CharField(max_length=500, blank=True)
    twitch = models.CharField(max_length=500, blank=True)
    spotify = models.CharField(max_length=500, blank=True)
    premium = models.BooleanField(default=False, blank=True)
    
    def __str__(self):
        return self.user.username


class ConnectionHistory(models.Model):
    ONLINE = 'online'
    OFFLINE = 'offline'
    AWAY = 'away'
    STATUS = (
        (ONLINE, 'On-line'),
        (OFFLINE, 'Off-line'),
        (AWAY, 'away'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections')
    session = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS, default=ONLINE)
    first_login = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "session"),)


class UserTab(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='name')
    connection = models.ForeignKey(ConnectionHistory, on_delete=models.CASCADE, null=True, related_name='tabs')
    date_added = models.DateTimeField(auto_now_add=True, null=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()