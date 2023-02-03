from django.contrib import admin
from .models import Room, Channel, Message, Log


admin.site.register(Room)
admin.site.register(Channel)
admin.site.register(Message)
admin.site.register(Log)