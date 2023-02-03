from django.urls import path

from . import consumers


urlpatterns = [
	path("ws/chat/<int:channel>/", consumers.ChatConsumer.as_asgi()),
]