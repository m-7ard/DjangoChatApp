from django.urls import path

from . import views

urlpatterns = [
	path('self/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('self/private-chat/<int:pk>/', views.PrivateChatDetailView.as_view(), name='private-chat'),
    path('self/create/private-chat/', views.CreatePrivateChat.as_view(), name='create-private-chat'),
    
    path('create/group-chat/', views.GroupChatCreateView.as_view(), name='create-group-chat'),
    path('group-chat/<int:pk>/', views.GroupChatDetailView.as_view(), name='group-chat'),
    path('create/category/<int:group_chat_pk>/', views.CategoryCreateView.as_view(), name='create-category'),
    path('create/group-channel/<int:group_chat_pk>/', views.GroupChannelCreateView.as_view(), name='create-group-channel'),
    path('create/group-channel/<int:group_chat_pk>/<int:category_pk>/', views.GroupChannelCreateView.as_view(), name='create-group-channel'),
    path('group-chat/<int:group_chat_pk>/group-channel/<int:group_channel_pk>/', views.GroupChannelDetailView.as_view(), name='group-channel'),

    path('add-friend/', views.FriendshipFormView.as_view(), name='add-friend'),
    path('group-chat/<int:group_chat_pk>/invite-users/', views.InviteFormView.as_view(), name='invite-users'),
    path('invite/<uuid:directory>/', views.InviteDetailView.as_view(), name='invite'),
    path('group-chat/<int:group_chat_pk>/leave/', views.GroupChatMembershipDeleteView.as_view(), name='leave-group-chat'),
    path('get-mentionables/<str:mention>', views.GetMentionables.as_view(), name='get-mentionables'),
]