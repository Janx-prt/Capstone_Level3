from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from newsroom.models import Article, Publisher
from .serializers import ArticleSerializer, PublisherSerializer
from .permissions import IsJournalist, IsEditor


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("publisher", "author")
    serializer_class = ArticleSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "mine", "subscribed"]:
            return [permissions.IsAuthenticated()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsJournalist()]
        if self.action == "approve":
            return [IsEditor()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not user.is_authenticated:
            return qs.filter(status=Article.Status.APPROVED)
        if user.is_superuser or user.is_staff:
            return qs
        if hasattr(user, "is_editor") and user.is_editor():
            return qs
        if hasattr(user, "is_journalist") and user.is_journalist():
            return qs.filter(Q(author=user) | Q(status=Article.Status.APPROVED)).distinct()
        return qs.filter(status=Article.Status.APPROVED)

    def perform_create(self, serializer):
        u = self.request.user
        if not (hasattr(u, "is_journalist") and u.is_journalist()) and not (u.is_staff or u.is_superuser):
            raise PermissionDenied("Only journalists can create articles.")
        serializer.save(author=u, status=Article.Status.PENDING)

    def perform_update(self, serializer):
        u = self.request.user
        obj: Article = self.get_object()
        if not (u.is_superuser or u.is_staff):
            if hasattr(u, "is_editor") and u.is_editor():
                pass
            elif hasattr(u, "is_journalist") and u.is_journalist():
                if obj.author_id != u.id:
                    raise PermissionDenied(
                        "You can only modify your own articles.")
            else:
                raise PermissionDenied("Not allowed.")
        serializer.save()

    def perform_destroy(self, instance):
        u = self.request.user
        if not (u.is_superuser or u.is_staff):
            if hasattr(u, "is_editor") and u.is_editor():
                pass
            elif hasattr(u, "is_journalist") and u.is_journalist():
                if instance.author_id != u.id:
                    raise PermissionDenied(
                        "You can only delete your own articles.")
            else:
                raise PermissionDenied("Not allowed.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        article = self.get_object()
        if article.status != Article.Status.APPROVED:
            article.status = Article.Status.APPROVED
            if not article.approved_at:
                article.approved_at = timezone.now()
            article.save(update_fields=["status", "approved_at"])
            return Response({"status": "approved", "approved_at": article.approved_at}, status=status.HTTP_200_OK)
        return Response({"status": "already_approved", "approved_at": article.approved_at}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        u = request.user
        qs = self.get_queryset().filter(author=u) if hasattr(
            u, "is_journalist") and u.is_journalist() else Article.objects.none()
        page = self.paginate_queryset(qs.order_by("-created_at"))
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def subscribed(self, request):
        u = request.user
        qs = Article.objects.filter(status=Article.Status.APPROVED)
        if hasattr(u, "is_reader") and u.is_reader():
            qs = qs.filter(
                Q(publisher__in=u.subscriptions_to_publishers.all()) |
                Q(author__in=u.subscriptions_to_journalists.all())
            ).distinct()
        else:
            qs = Article.objects.none()
        qs = qs.order_by("-approved_at", "-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticated]
