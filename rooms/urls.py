from django.urls import path
from .views import DashboardView, RoomView, ChannelView


urlpatterns = [
	path('dashboard/', DashboardView.as_view(), name='dashboard'),
	path('<int:room>/', RoomView.as_view(), name='room'),
	path('<int:room>/<int:channel>', ChannelView.as_view(), name='channel'),
]