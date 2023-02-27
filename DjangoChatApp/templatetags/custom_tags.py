from django.template.defaulttags import register

from rooms.models import Member

@register.filter(name='user_is_member')
def user_is_member(user, room):
    return Member.objects.filter(user=user, room=room).first()
