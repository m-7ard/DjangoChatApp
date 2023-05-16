from django.urls import path
from .views import FrontpageView, RequestData, GetViewByName, GetHtmlElementFromModel, GetHtmlElementFromData


urlpatterns = [
	path('', FrontpageView.as_view(), name='frontpage'),
    path('RequestData/', RequestData.as_view(), name='RequestData'),
    path('GetViewByName/<str:name>/', GetViewByName),
    path('GetHtmlElementFromModel/', GetHtmlElementFromModel.as_view()),
]