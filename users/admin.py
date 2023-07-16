from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Friendship, CustomUser, CustomUserManager
from django.forms import TextInput, Textarea
    
	
admin.site.register(CustomUser)
admin.site.register(Friendship)