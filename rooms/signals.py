from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_delete
from django.db import models
from DjangoChatApp.settings import MEDIA_URL

from .models import GroupChannel, Category


# def decrease_relative_order(sender, instance, **kwargs):
#     print('\n*' * 5)
# 
# post_delete.connect(decrease_relative_order, GroupChannel)
# post_delete.connect(decrease_relative_order, Category)