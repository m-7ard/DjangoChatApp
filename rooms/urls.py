from django.urls import path

from . import views

urlpatterns = [
	path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('create/group-chat/', views.CreateGroupChat.as_view(), name='create-group-chat'),
    
]