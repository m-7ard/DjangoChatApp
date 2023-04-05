from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile
from django.forms import TextInput, Textarea

class ProfileInline(admin.StackedInline):
    model = Profile
    
class UserAdmin(admin.ModelAdmin):
    inlines = (ProfileInline,)
    search_fields = ['email', 'username']
    list_display = ['username', 'email', 'date_joined', 'get_premium']
    ordering = ['-date_joined']

    @admin.display(description='Premium User')
    def get_premium(self, user):
        return user.profile.premium

    

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Profile)
