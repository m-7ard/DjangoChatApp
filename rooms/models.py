from django.db import models
from django.contrib.auth.models import User

from PIL import Image


class Room(models.Model):
    name = models.CharField(max_length=50, blank=False)
    description = models.CharField(max_length=60, blank=True)
    owner = models.ForeignKey(User, related_name='servers_owned', null=True, on_delete=models.SET_NULL)
    image = models.ImageField(default='blank.png')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}'
    
    def members_by_users(self):
        return self.members.all()


class Channel(models.Model):
    room = models.ForeignKey(Room, related_name='channels', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=30, blank=False)
    description = models.CharField(max_length=60, blank=True)
    display_logs = models.ManyToManyField('Action')
    
    def __str__(self):
        return f'{self.room}: {self.name}'

    def display_actions(self):
        return [action.name for action in self.display_logs.all()]


class Role(models.Model):
    name = models.CharField(max_length=50, blank=False, default='Role')
    hierarchy = models.IntegerField(default=10)
    room = models.ForeignKey(Room, related_name='roles', on_delete=models.CASCADE, null=True)
    color = models.CharField(default='#e0dbd1', max_length=7)

    can_create_message = models.BooleanField(default=True)
    can_delete_own_message = models.BooleanField(default=True)
    can_delete_lower_message = models.BooleanField(default=False)
    can_delete_higher_message = models.BooleanField(default=False)
    
    can_edit_own_message = models.BooleanField(default=True)
    can_edit_lower_message = models.BooleanField(default=False)
    can_edit_higher_message = models.BooleanField(default=False)

    can_create_channel = models.BooleanField(default=False)
    can_edit_channel = models.BooleanField(default=False)
    can_delete_channel = models.BooleanField(default=False)

    can_view_channels = models.ManyToManyField(Channel, related_name='viewable_by_roles', blank=True)


class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='memberships')
    roles = models.ManyToManyField(Role, related_name='members')
    room = models.ForeignKey(Room, related_name='members', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=30, blank=True)
    
    def __str__(self):
        return self.user.username
    
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")


class Message(models.Model):
    content = models.CharField(max_length=1000, blank=False)
    member = models.ForeignKey(Member, related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.ForeignKey(Channel, related_name='messages', on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('date_added',)
    
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")

    def instance(self):
        return 'message'

        
class Action(models.Model):
    name = models.CharField(max_length=20)
    display_name = models.CharField(max_length=20)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.name}: {self.description}'


class Log(models.Model):
    action = models.ForeignKey(Action, related_name='logs', on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, related_name='logs', on_delete=models.CASCADE, null=True)
    target_user = models.ForeignKey(User, related_name='room_activity', on_delete=models.SET_NULL, null=True)
    trigger_user = models.ForeignKey(User, related_name='room_actions', on_delete=models.SET_NULL, null=True)
    date_added = models.DateTimeField(auto_now_add=True, null=True)

    # if the action model were deleted, this would remain
    action_display_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ('date_added',)
        
    def display_date(self):
        return self.date_added.strftime("%H:%M:%S")
    
    def instance(self):
        return 'log'


class Reaction(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reactions')
    name = models.CharField(max_length=20)
    image = models.ImageField()

    def save(self):
        super().save()
        img = Image.open(self.image.path)
        new_img = (24, 24)
        img.thumbnail(new_img)
        img.save(self.image.path)


class MessageReaction(models.Model):
	message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
	reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
	users = models.ManyToManyField(User, blank=True)
	
	def add_user(self, user):
		self.users.add(user)
	
	def remove_user(self, user):
		self.users.remove(user)
		if len(self.users) == 0:
			self.delete()
	
	def image(self):
		return self.reaction.image