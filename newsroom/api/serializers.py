"""
Serializers for the Newsroom API.

This module defines serializers for:

- :class:`~newsroom.models.Publisher`
- :class:`~newsroom.models.Article`

They transform model instances into JSON representations and handle
validation for incoming data.
"""

from rest_framework import serializers
from newsroom.models import Article, Publisher


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`~newsroom.models.Publisher`.

    Fields
    ------
    id : int
        Primary key of the publisher.
    name : str
        Name of the publisher.
    description : str
        Optional description of the publisher.
    """

    class Meta:
        model = Publisher
        fields = ["id", "name", "description"]


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`~newsroom.models.Article`.

    Includes nested publisher representation (read-only),
    related author string, and an extra ``publisher_id`` field
    for write operations.

    Fields
    ------
    id : int
        Primary key of the article.
    title : str
        Title of the article.
    body : str
        Main content of the article.
    cover_url : str
        Optional cover image URL.
    status : str
        Workflow status (Draft, Pending, Approved, Rejected).
    publisher : PublisherSerializer
        Nested publisher representation (read-only).
    publisher_id : int
        Primary key of the publisher (write-only).
    author : str
        String representation of the author (read-only).
    author_username : str
        Username of the author (read-only).
    created_at : datetime
        Timestamp of creation (read-only).
    updated_at : datetime
        Timestamp of last update (read-only).
    approved_at : datetime
        Timestamp of approval (read-only).
    """

    publisher = PublisherSerializer(read_only=True)
    author = serializers.StringRelatedField(read_only=True)
    author_username = serializers.ReadOnlyField(source="author.username")
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(), write_only=True, source="publisher"
    )

    class Meta:
        model = Article
        fields = [
            "id", "title", "body", "cover_url", "status",
            "publisher", "publisher_id",
            "author", "author_username",
            "created_at", "updated_at", "approved_at",
        ]
        read_only_fields = ["status", "author",
                            "created_at", "updated_at", "approved_at"]
