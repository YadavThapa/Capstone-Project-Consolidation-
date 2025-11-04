"""
Simplified URL configuration for news_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from news_app.admin_views import admin_access_check

urlpatterns = [
    # Custom admin protection - check permissions before allowing access
    path('admin/', admin_access_check, name='admin_protection'),
    path('django-admin/', admin.site.urls, name='django_admin'),
    path('', include('news_app.urls')),
    # Authentication URLs for login/logout functionality
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
