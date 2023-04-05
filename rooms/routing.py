from django.urls import path, re_path

from . import consumers


urlpatterns = [
	re_path("ws/chat/(?P<room>\d+)/(?P<channel>\d+)/", consumers.ChatConsumer.as_asgi()),
	re_path("ws/chat/(?P<room>\d+)/", consumers.ChatConsumer.as_asgi()),
	re_path("ws/any/", consumers.ChatConsumer.as_asgi()),
]