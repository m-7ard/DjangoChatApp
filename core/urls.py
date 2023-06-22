from django.urls import path
from .views import (
    FrontpageView, 
    GetViewByName, 
    GetTooltip,
    GetOverlay,
)


urlpatterns = [
	path('', FrontpageView.as_view(), name='frontpage'),
    path('GetViewByName/<str:name>/', GetViewByName),
    path('tooltip/<str:id>/', GetTooltip.as_view()),
    path('overlay/<str:id>/', GetOverlay.as_view()),
]