from django.urls import path
from .views import (
    FrontpageView, 
    GetViewByName, 
    GetTemplate
)


urlpatterns = [
	path('', FrontpageView.as_view(), name='frontpage'),
    path('GetViewByName/<str:name>/', GetViewByName),
    path('GetTemplate/', GetTemplate.as_view())
]