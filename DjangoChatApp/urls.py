from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from . import settings


urlpatterns = [
	path('', include('core.urls')),
	path('users/', include('users.urls')),
	path('rooms/', include('rooms.urls')),
    path('admin/', admin.site.urls),
]


if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
