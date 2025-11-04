"""REST serializers for news_app models.

This module contains ModelSerializers for the main news application models:
CustomUser, Publisher, Article and Newsletter. Docstrings were added and
long lines wrapped to satisfy style checks while preserving existing
behavior.
"""

from rest_framework import serializers
from .models import Article, Publisher, CustomUser, Newsletter


class UserSerializer(serializers.ModelSerializer):
    """Serialize CustomUser fields used by the API."""

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "bio",
        ]


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize Publisher and include approved article count."""

    article_count = serializers.SerializerMethodField()

    class Meta:
        model = Publisher
        fields = [
            "id",
            "name",
            "description",
            "website",
            "founded_date",
            "created_at",
            "article_count",
        ]

    def get_article_count(self, obj):
        return obj.articles.filter(is_approved=True).count()


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize Article with nested read-only author and publisher."""

    author = UserSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "summary",
            "author",
            "publisher",
            "status",
            "is_approved",
            "tags",
            "views_count",
            "created_at",
            "published_at",
            "featured_image",
        ]
        read_only_fields = [
            "slug",
            "is_approved",
            "views_count",
            "published_at",
        ]


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize Newsletter with its author and publisher."""

    author = UserSerializer(read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "is_independent",
            "created_at",
            "sent_at",
        ]
