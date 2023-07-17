from django.urls import path

from . import views

urlpatterns = [
	path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('group-chat/create/', views.CreateGroupChat.as_view(), name='create-group-chat'),
    path('group-chat/<int:pk>/', views.GroupChatDetailView.as_view(), name='group-chat'),
    
]