"""
Django REST Framework API views for the news application.

This module provides API endpoints for:
- Articles: Read-only access with subscription-based filtering
- Publishers: Read-only access and subscription management
- Journalists: Subscription management for journalist users
- Authentication: Token generation for API access

All endpoints require token authentication except for token generation.
"""
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db import models
from django.contrib.auth import authenticate
from .models import Article, Publisher, CustomUser
from .serializers import ArticleSerializer, PublisherSerializer, UserSerializer

# pylint: disable=no-member,broad-exception-caught
# Django models have 'objects' manager and 'DoesNotExist' exception
# Broad exceptions needed for API error handling


class IsAPIClient(permissions.BasePermission):
    """Custom permission for API clients"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for articles
    Filters articles based on user's subscriptions
    """
    serializer_class = ArticleSerializer
    permission_classes = [IsAPIClient]

    def get_queryset(self):
        """Return only approved articles.

        For reader users this is limited to their subscriptions.
        """
        user = self.request.user

        # Base queryset: only approved articles
        queryset = Article.objects.filter(is_approved=True, status='approved')

        # Filter based on subscriptions
        if user.role == 'reader':
            # Get subscribed publishers and journalists
            subscribed_publishers = user.subscribed_publishers.all()
            subscribed_journalists = user.subscribed_journalists.all()

            # Filter articles
            queryset = queryset.filter(
                models.Q(publisher__in=subscribed_publishers)
                |
                models.Q(author__in=subscribed_journalists)
            )

        return queryset.distinct()

    @action(detail=False, methods=['get'], url_path='by_publisher')
    def by_publisher(self, request, publisher_id=None):
        """Get articles by specific publisher"""
        try:
            publisher_id = request.query_params.get('publisher_id')
            if publisher_id:
                articles = self.get_queryset().filter(
                    publisher_id=publisher_id
                )
                page = self.paginate_queryset(articles)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                serializer = self.get_serializer(articles, many=True)
                return Response(serializer.data)
            return Response({'error': 'publisher_id required'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['get'], url_path='by_journalist')
    def by_journalist(self, request, journalist_id=None):
        """Get articles by specific journalist"""
        try:
            journalist_id = request.query_params.get('journalist_id')
            if journalist_id:
                articles = self.get_queryset().filter(author_id=journalist_id)
                page = self.paginate_queryset(articles)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                serializer = self.get_serializer(articles, many=True)
                return Response(serializer.data)
            return Response({'error': 'journalist_id required'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for publishers"""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAPIClient]


class PublisherSubscriptionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Manage subscriptions to publishers for the authenticated user.

    POST /api/subscriptions/publishers/ {"publisher_id": <id>} -> subscribe
    DELETE /api/subscriptions/publishers/<pk>/ -> unsubscribe
    GET /api/subscriptions/publishers/ -> list subscriptions
    """
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAPIClient]

    def get_queryset(self):
        # Return the publishers the requesting user is subscribed to
        return self.request.user.subscribed_publishers.all()

    def create(self, request, *args, **kwargs):
        publisher_id = request.data.get('publisher_id') or \
            request.query_params.get('publisher_id')
        if not publisher_id:
            return Response({'error': 'publisher_id required'}, status=400)
        try:
            publisher = Publisher.objects.get(pk=publisher_id)
        except Publisher.DoesNotExist:
            return Response({'error': 'publisher not found'}, status=404)

        user = request.user
        user.subscribed_publishers.add(publisher)
        serializer = self.get_serializer(publisher)
        return Response(serializer.data, status=201)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        pk = kwargs.get('pk')
        try:
            publisher = Publisher.objects.get(pk=pk)
        except Publisher.DoesNotExist:
            return Response(status=404)
        user.subscribed_publishers.remove(publisher)
        return Response(status=204)


class JournalistSubscriptionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Manage subscriptions to journalists (users with role='journalist')."""
    queryset = CustomUser.objects.filter(role='journalist')
    serializer_class = UserSerializer
    permission_classes = [IsAPIClient]

    def get_queryset(self):
        return self.request.user.subscribed_journalists.all()

    def create(self, request, *args, **kwargs):
        journalist_id = (
            request.data.get('journalist_id') or
            request.query_params.get('journalist_id')
        )
        if not journalist_id:
            return Response({'error': 'journalist_id required'}, status=400)
        try:
            journalist = CustomUser.objects.get(
                pk=journalist_id,
                role='journalist',
            )
        except CustomUser.DoesNotExist:
            return Response({'error': 'journalist not found'}, status=404)

        user = request.user
        user.subscribed_journalists.add(journalist)
        serializer = self.get_serializer(journalist)
        return Response(serializer.data, status=201)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        pk = kwargs.get('pk')
        try:
            journalist = CustomUser.objects.get(pk=pk, role='journalist')
        except CustomUser.DoesNotExist:
            return Response(status=404)
        user.subscribed_journalists.remove(journalist)
        return Response(status=204)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def generate_api_token(request):
    """Generate API token for third-party clients"""
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': 'Username and password required'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_400_BAD_REQUEST)
