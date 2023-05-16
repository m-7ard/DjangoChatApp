from django.urls import path
from .views import (
    DashboardView, 
	RoomView, 
	ChannelView, 
	ChannelCreateView, 
	RoomCreateView,
    ChannelEditView,
	RoomUpdateView,
    get_html_form,
)

urlpatterns = [
    path('get_html_form/<str:form_name>', get_html_form, name="rooms-get_html_form"),
	path('dashboard/', DashboardView.as_view(), name='dashboard'),
	path('<int:room>/', RoomView.as_view(), name='room'),
	path('<int:room>/<int:channel>/', ChannelView.as_view(), name='channel'),
	path('create/room/', RoomCreateView.as_view(), name="create-room"),
	path('create/channel/<int:room>', ChannelCreateView.as_view(), name='create-channel'),
	path('update/room/<int:room>/', RoomUpdateView.as_view(), name='update-room'),
    path('update/channel/<int:channel>/', ChannelEditView.as_view(), name='edit-channel'),
]