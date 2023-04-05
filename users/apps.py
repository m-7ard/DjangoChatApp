import datetime

from django.utils import timezone
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # If there was a server crash or something, we want to set all the still online users to offline
        from .models import Profile
        time_barrier = timezone.make_aware(datetime.datetime.now() - datetime.timedelta(seconds=10), timezone.get_default_timezone())
        Profile.objects.filter(status='online', last_ping__lt=time_barrier).update(status='offline')