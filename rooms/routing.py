from django.urls import path, re_path

from . import consumers


urlpatterns = [
	path("ws/app/", consumers.ChatConsumer.as_asgi()),
    path("ws/app/group-chat/<int:group_chat_pk>/", consumers.GroupChatConsumer.as_asgi()),
    path("ws/app/group-chat/<int:group_chat_pk>/<int:group_channel_pk>/", consumers.GroupChatConsumer.as_asgi()),

]