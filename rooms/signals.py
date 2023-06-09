from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_delete
from DjangoChatApp.settings import MEDIA_URL

from .models import Room, Channel, Role, Message, Member, Log, Action, ChannelCategory
from utils import create_send_to_group


"""

NOTE: there's an error at the time of room creation, fix

"""


@receiver(post_save, sender=Room)
def create_room_default_foreignkeys(sender, created, instance, **kwargs):
    if created:
        default_category = ChannelCategory.objects.create(
            room=instance,
            name='Text Channels',
            order=0,
        )

        default_channel = Channel.objects.create(
            room=instance,
            name='general',
            description='default channel',
            category=default_category,
        )

        default_channel.display_logs.set(Action.objects.all())
        default_channel.save()

        default_role = Role.objects.create(
            room=instance,
            name='all',
            color='#e0dbd1',
            default=True
        )

        owner_member = Member.objects.create(
            user=instance.owner,
            room=instance
        )

        owner_member.roles.add(default_role)


@receiver(post_save, sender=Member)
def assign_default_role(sender, created, instance, **kwargs):
    if created:
        print(instance, '------------\n' * 20, instance.room.default_role)
        instance.roles.add(instance.room.default_role)
        instance.save()

