from rest_framework import serializers
from newsroom.models import Article, Publisher


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "description"]


class ArticleSerializer(serializers.ModelSerializer):
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
