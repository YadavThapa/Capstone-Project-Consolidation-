"""
URL configuration for the news_app Django application.
Defines all routes for views, API endpoints, and admin features.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from . import admin_views
from . import email_tracking
from .api_views import (
     ArticleViewSet,
     PublisherViewSet,
     PublisherSubscriptionViewSet,
     JournalistSubscriptionViewSet,
     generate_api_token,
)

# Create a router and register API viewsets
router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(
     r'subscriptions/publishers',
     PublisherSubscriptionViewSet,
     basename='publisher-subscription'
)
router.register(
     r'subscriptions/journalists',
     JournalistSubscriptionViewSet,
     basename='journalist-subscription'
)

urlpatterns = [
     path('', views.article_list, name='article_list'),
     path('article/<slug:slug>/', views.article_detail, name='article_detail'),
     path('about/', views.about, name='about'),
     path('contact/', views.contact, name='contact'),
     path('signup/', views.signup, name='signup'),
     # Publisher URLs
     path('publishers/', views.publisher_list, name='publisher_list'),
     path(
          'publisher/<int:pk>/',
          views.publisher_detail,
          name='publisher_detail',
     ),
     path(
          'publisher/<int:pk>/toggle-subscription/',
          views.toggle_publisher_subscription,
          name='toggle_publisher_subscription',
     ),
     # Journalist URLs
     path('journalists/', views.journalist_list, name='journalist_list'),
     path(
          'journalist/<int:pk>/',
          views.journalist_detail,
          name='journalist_detail',
     ),
     path(
          'journalist/<int:pk>/toggle-subscription/',
          views.toggle_journalist_subscription,
          name='toggle_journalist_subscription',
     ),
     # Profile URLs
     path('profile/', views.profile, name='profile'),
     path('profile/edit/', views.edit_profile, name='edit_profile'),
     # Email tracking URLs - Production ready with hex token validation
     path(
          'track-email/<str:token>/',
          email_tracking.track_email_open,
          name='track_email_open',
     ),
     path(
          'mark-read/<int:notification_id>/',
          email_tracking.mark_notification_read,
          name='mark_notification_read',
     ),
     # Admin approval management URLs
     path(
          'admin-dashboard/',
          admin_views.admin_dashboard,
          name='admin_dashboard',
     ),
     path(
          'admin/articles/',
          admin_views.article_approval_list,
          name='admin_article_approval_list',
     ),
     path(
          'admin/article/<int:article_id>/',
          admin_views.article_detail_admin,
          name='admin_article_detail',
     ),
     path(
          'admin/article/<int:article_id>/approve/',
          admin_views.approve_article_admin,
          name='admin_approve_article',
     ),
     path(
          'admin/article/<int:article_id>/reject/',
          admin_views.reject_article_admin,
          name='admin_reject_article',
     ),

     # ==========================================
     # RESTful API endpoints for third-party clients
     # ==========================================

     # API endpoints
     path('api/', include(router.urls)),

     # Custom token generation endpoint
     path(
          'api/auth/generate-token/',
          generate_api_token,
          name='generate_api_token',
     ),

     # Authentication endpoint for obtaining tokens (Django's default)
     path('api-token-auth/', obtain_auth_token, name='api_token_auth'),

     # API browsable interface (for development/testing)
     path(
          'api-auth/',
          include('rest_framework.urls', namespace='rest_framework'),
     ),
]
"""
URL configuration for the news_app Django application.
Defines all routes for views, API endpoints, and admin features.
"""
