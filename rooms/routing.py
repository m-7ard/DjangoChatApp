from django.urls import path, re_path

from . import consumers


urlpatterns = [
    
	re_path("ws/app/", consumers.ChatConsumer.as_asgi()),
]