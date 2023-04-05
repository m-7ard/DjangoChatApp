import time

from django.apps import AppConfig
from threading import Thread



class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

