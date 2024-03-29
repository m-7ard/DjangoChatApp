from django.urls import path

from . import views

urlpatterns = [
	path('self/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('self/private-chat/<int:pk>/', views.PrivateChatDetailView.as_view(), name='private-chat'),
    path('self/get-private-chat/', views.PrivateChatGetOrCreateView.as_view(), name='get-or-create-private-chat'),
    
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
    path('group-chat/<int:group_chat_pk>/roles/manage/', views.RoleManageView.as_view(), name='manage-roles'),
    path('group-chat/<int:group_chat_pk>/roles/create/', views.RoleCreateView.as_view(), name='create-role'),
    path('group-chat/<int:group_chat_pk>/roles/order/', views.RoleOrderUpdateView.as_view(), name='update-role-order'),
    path('role/<int:pk>', views.RoleUpdateView.as_view(), name='edit-role'),
    path('role/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='delete-role'),
    path('role/<int:pk>/members/manage/', views.RoleManageMembersView.as_view(), name='manage-role-members'),

    path('backlog-group/<int:backlog_group_pk>/profile-card/<int:user_pk>', views.UserProfileCardView.as_view(), name='user-profile-card'),
    path('profile-card/<int:user_pk>', views.UserProfileCardView.as_view(), name='user-profile-card'),
    
    path('emote/<int:pk>/edit/', views.EmoteUpdateView.as_view(), name='edit-emote'),
    path('emote/<int:pk>/delete/', views.EmoteDeleteView.as_view(), name='delete-emote'),
    
    path('emote-menu/<int:group_chat_pk>/', views.EmoteMenuView.as_view(), name='emote-menu'),
    path('emote-menu/', views.EmoteMenuView.as_view(), name='emote-menu', kwargs={'group_chat_pk': None}),
]