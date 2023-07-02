from django.urls import path

from . import views

urlpatterns = [
	path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
	path('<int:pk>/', views.RoomView.as_view(), name='room'),
    path('<int:room>/leave/', views.LeaveRoom.as_view(), name='leave-room'),
    path('<int:room>/join/', views.JoinRoom.as_view(), name='join-room'),
	path('<int:room>/<int:channel>/', views.ChannelView.as_view(), name='channel'),
	path('create/room/', views.RoomCreateView.as_view(), name="create-room"),
	
    path('manage/room/<int:pk>/', views.RoomManageView.as_view(), name='manage-room'),
	path('update/room/<int:pk>/', views.RoomUpdateView.as_view(), name='update-room'),

    path('room/<int:pk>/create/channel/', views.ChannelCreateView.as_view(), name='create-channel'),
    path('manage/channel/<int:pk>/', views.ChannelManageView.as_view(), name='manage-channel'),
    path('update/channel/<int:pk>/', views.ChannelUpdateView.as_view(), name='update-channel'),
    path('delete/channel/<int:pk>/', views.ChannelDeleteView.as_view(), name='delete-channel'),

    path('delete/room/<int:pk>/', views.DeleteRoom.as_view(), name='delete-room'),
    path('explore/', views.RoomListView.as_view(), name='explore-rooms'),
    
    path('update/permissions/<int:pk>', views.ModelPermissionGroupUpdateView.as_view(), name='update-model-permissions'),
]