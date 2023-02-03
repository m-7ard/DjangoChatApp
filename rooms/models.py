from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
	name = models.CharField(max_length=50, blank=False)
	description = models.CharField(max_length=60, blank=True)
	members = models.ManyToManyField(User, related_name='joined_rooms', blank=True)
	
	def __str__(self):
		return f'{self.name}'


class Channel(models.Model):
	name = models.CharField(max_length=30, blank=False)
	description = models.CharField(max_length=60, blank=True)
	room = models.ForeignKey(Room, related_name='channels', blank=False, null=True, on_delete=models.CASCADE)
	
	def __str__(self):
		return f'{self.room}: {self.name}'


class Message(models.Model):
	content = models.CharField(max_length=1000, blank=False)
	user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE, null=True)
	channel = models.ForeignKey(Channel, related_name='messages', on_delete=models.CASCADE, null=True)
	date_added = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('date_added',)
	
	def display_date(self):
		return self.date_added.strftime("%H:%M:%S")

	def instance(self):
		return 'message'

class Log(models.Model):
	action = models.CharField(max_length=30)
	room = models.ForeignKey(Room, related_name='member_log', on_delete=models.CASCADE, null=True)
	user = models.ForeignKey(User, related_name='server_log', on_delete=models.CASCADE, null=True)
	date_added = models.DateTimeField(auto_now_add=True, null=True)

	class Meta:
		ordering = ('date_added',)
		
	def display_date(self):
		return self.date_added.strftime("%H:%M:%S")

	def instance(self):
		return 'log'