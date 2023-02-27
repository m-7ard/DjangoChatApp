from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from .models import Room, Channel, Role, Message, Member, Log, Action, MessageReaction

@receiver(post_save, sender=Room)
def create_room_default_foreignkeys(sender, created, instance, **kwargs):
	if created:
		default_channel = Channel.objects.create(
			room=instance,
			name='general',
			description='',
		)
		default_channel.display_logs.set(Action.objects.all())
		default_channel.save()

		default_role = Role.objects.create(
			room=instance,
			name='Role #1',
		)

		Member.objects.create(
			user=instance.owner,
			room=instance
		)

@receiver(post_save, sender=Message)
def assign_member_to_message(sender, created, instance, **kwargs):
	if created:
		instance.member = Member.objects.get(
			user=instance.user,
			room=instance.channel.room,
		)
		instance.save()

@receiver(post_save, sender=Log)
def assign_readable_action_to_log(sender, created, instance, **kwargs):
	if created:
		instance.action_display_name = instance.action.display_name
		instance.save()
