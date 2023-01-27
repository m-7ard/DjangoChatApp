from django.urls import path
from .views import SignupView, SigninView, SignoutView


urlpatterns = [
	path('signup/', SignupView.as_view(), name='signup'),
	path('signin/', SigninView.as_view(), name='signin'),
	path('signout/', SignoutView.as_view(), name='signout'),
]