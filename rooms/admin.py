from django.contrib import admin
from .models import Room, Channel, Message, Log, Role, Member, Action, Reaction, Emote, ChannelCategory


class RoleInline(admin.StackedInline):
    model = Role
    extra = 0

    fieldsets = (
        (None, {
            'fields': (('name', 'room', 'hierarchy'))
            }),
        (None, {
            'fields': (('can_create_message', 'can_delete_own_message', 'can_delete_lower_message', 'can_delete_higher_message'),)
            }),
		(None, {
            'fields': (('can_edit_own_message', 'can_edit_lower_message', 'can_edit_higher_message'),)
            }),
		(None, {
            'fields': (('can_create_channel', 'can_edit_channel', 'can_delete_channel'),)
            }),
        (None, {
            'fields': ('can_view_channels',)
            }),
    )


class RoomAdmin(admin.ModelAdmin):
    inlines = [RoleInline]
    list_display = ('id', 'name', 'description', 'owner')
    

admin.site.register(Room, RoomAdmin)
admin.site.register(Channel)
admin.site.register(Message)
admin.site.register(Log)
admin.site.register(Role)
admin.site.register(Member)
admin.site.register(Action)
admin.site.register(Reaction)
admin.site.register(Emote)
admin.site.register(ChannelCategory)