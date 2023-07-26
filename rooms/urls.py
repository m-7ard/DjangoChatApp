from django.urls import path

from . import views

urlpatterns = [
	path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('create/group-chat/', views.CreateGroupChat.as_view(), name='create-group-chat'),
    path('group-chat/<int:pk>/', views.GroupChatDetailView.as_view(), name='group-chat'),
    path('create/category/<int:group_chat_pk>/', views.CategoryCreateView.as_view(), name='create-category'),
    path('create/group-channel/<int:group_chat_pk>/', views.GroupChannelCreateView.as_view(), name='create-group-channel'),
    path('create/group-channel/<int:group_chat_pk>/<int:category_pk>/', views.GroupChannelCreateView.as_view(), name='create-group-channel'),
    path('group-chat/<int:group_chat_pk>/group-channel/<int:group_channel_pk>/', views.GroupChannelDetailView.as_view(), name='group-channel'),

    path('add-friend/', views.FriendshipFormView.as_view(), name='add-friend'),
]