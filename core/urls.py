from django.urls import path
from .views import FrontpageView


urlpatterns = [
	path('', FrontpageView.as_view(), name='frontpage'),
]