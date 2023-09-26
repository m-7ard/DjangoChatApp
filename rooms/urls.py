from django.urls import path

from . import views

urlpatterns = [
	path('self/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('self/private-chat/<int:pk>/', views.PrivateChatDetailView.as_view(), name='private-chat'),
    path('self/create/private-chat/', views.PrivateChatFormView.as_view(), name='create-private-chat'),
    
    path('create/group-chat/', views.GroupChatCreateView.as_view(), name='create-group-chat'),
    path('group-chat/<int:pk>/', views.GroupChatDetailView.as_view(), name='group-chat'),
    path('create/category/<int:group_chat_pk>/', views.CategoryCreateView.as_view(), name='create-category'),
    path('create/group-channel/<int:group_chat_pk>/', views.GroupChannelCreateView.as_view(), name='create-group-channel'),
    path('create/group-channel/<int:group_chat_pk>/<int:category_pk>/', views.GroupChannelCreateView.as_view(), name='create-group-channel'),
    path('group-chat/<int:group_chat_pk>/group-channel/<int:group_channel_pk>/', views.GroupChannelDetailView.as_view(), name='group-channel'),

    path('add-friend/', views.FriendshipFormView.as_view(), name='add-friend'),

    path('group-chat/<int:group_chat_pk>/manage-invites/', views.GroupChatInviteManageView.as_view(), name='manage-group-chat-invites'),
    path('<str:kind>/<int:pk>/get-invite/', views.GetInviteView.as_view(), name='get-invite'),
    path('<str:kind>/<int:pk>/create-invite/', views.InviteCreateView.as_view(), name='create-invite'),
    path('invite/<int:pk>/', views.InviteDeleteView.as_view(), name='delete-invite'),

    path('group-chat/<int:group_chat_pk>/leave/', views.GroupChatLeaveView.as_view(), name='leave-group-chat'),
    path('group-chat/<int:group_chat_pk>/manage-emotes/', views.EmoteManageView.as_view(), name='manage-emotes'),
    path('group-chat/<int:group_chat_pk>/add-emote/', views.EmoteCreateView.as_view(), name='add-emote'),
    path('group-chat/<int:group_chat_pk>/profile-card/<int:user_pk>', views.GroupChatUserProfileCard.as_view(), name='group-chat-user-profile-card'),
    
    path('emote/<int:pk>/edit/', views.EmoteUpdateView.as_view(), name='edit-emote'),
    path('emote/<int:pk>/delete/', views.EmoteDeleteView.as_view(), name='delete-emote'),
    
    path('emote-menu/<int:group_chat_pk>/', views.EmoteMenuView.as_view(), name='emote-menu'),
    path('emote-menu/', views.EmoteMenuView.as_view(), name='emote-menu', kwargs={'group_chat_pk': None}),
    path('get-private-chat/', views.getOrCreatePrivateChat.as_view(), name='get-or-create-private-chat'),
]