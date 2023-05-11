"""
import datetime

from django.utils import timezone
from django.apps import AppConfig
from models import CustomUser


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # If there was a server crash or something, we want to set all the still online users to offline
        time_barrier = timezone.make_aware(datetime.datetime.now() - datetime.timedelta(seconds=10), timezone.get_default_timezone())
        CustomUser.objects.filter(status='online', last_ping__lt=time_barrier).update(status='offline')
"""