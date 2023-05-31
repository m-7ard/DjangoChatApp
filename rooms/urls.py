from django.urls import path

from . import views

urlpatterns = [
	path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
	path('<int:room>/', views.RoomView.as_view(), name='room'),
    path('<int:room>/leave/', views.LeaveRoom.as_view(), name='leave-room'),
    path('<int:room>/join/', views.JoinRoom.as_view(), name='join-room'),
	path('<int:room>/<int:channel>/', views.ChannelView.as_view(), name='channel'),
	path('create/room/', views.RoomCreateView.as_view(), name="create-room"),
	path('create/channel/<int:room>', views.ChannelCreateView.as_view(), name='create-channel'),
	path('update/room/<int:room>/', views.RoomUpdateView.as_view(), name='update-room'),
    path('update/channel/<int:channel>/', views.ChannelUpdateView.as_view(), name='update-channel'),
    path('delete/channel/<int:channel>/', views.ChannelDeleteView.as_view(), name='delete-channel'),
]