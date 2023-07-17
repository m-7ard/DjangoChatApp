from django.urls import path, re_path

from . import consumers


urlpatterns = [
	path("ws/app/", consumers.ChatConsumer.as_asgi()),
    # path("ws/app/<int:groupchat_pk>/")
]