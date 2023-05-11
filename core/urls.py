from django.urls import path
from .views import FrontpageView, RequestData, get_reverse_url, GetHtmlElementFromModel, GetHtmlElementFromData


urlpatterns = [
	path('', FrontpageView.as_view(), name='frontpage'),
    path('RequestData/', RequestData.as_view(), name='RequestData'),
    path('get_reverse_url/<str:name>/', get_reverse_url),
    path('GetHtmlElementFromModel/', GetHtmlElementFromModel.as_view()),
]