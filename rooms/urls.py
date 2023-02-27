from django.urls import path
from .views import DashboardView, RoomView, ChannelView, ChannelCreateView, RoomCreateView


urlpatterns = [
	path('dashboard/', DashboardView.as_view(), name='dashboard'),
	path('<int:room>/', RoomView.as_view(), name='room'),
	path('<int:room>/<int:channel>/', ChannelView.as_view(), name='channel'),
	path('<int:room>/create/', ChannelCreateView.as_view(), name='create-channel'),
	path('create/', RoomCreateView.as_view(), name="create-room"),
]