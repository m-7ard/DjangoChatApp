from django.urls import path
from .views import FrontpageView, RequestData, get_reverse_url


urlpatterns = [
	path('', FrontpageView.as_view(), name='frontpage'),
    path('RequestData/', RequestData.as_view(), name='RequestData'),
    path('get_reverse_url/<str:name>/', get_reverse_url),
]