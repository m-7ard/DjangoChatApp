from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_delete
from django.db import models
from DjangoChatApp.settings import MEDIA_URL

from utils import create_send_to_group