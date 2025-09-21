"""
API viewsets for the Newsroom application.

This module defines viewsets for articles and publishers with
role-based permissions and custom actions.

- :class:`ArticleViewSet` – CRUD operations, approval workflow, and
  personalized article queries.
- :class:`PublisherViewSet` – Read-only access to publishers.
"""

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
    """
    Viewset for managing :class:`~newsroom.models.Article` instances.

    Provides default CRUD actions along with custom actions
    for approving, listing personal articles, and listing
    subscribed articles. Enforces role-based permissions.

    Attributes
    ----------
    queryset : QuerySet
        Default queryset with related publisher and author preloaded.
    serializer_class : ArticleSerializer
        Serializer used for articles.
    """

    queryset = Article.objects.select_related("publisher", "author")
    serializer_class = ArticleSerializer

    def get_permissions(self):
        """
        Return appropriate permissions depending on the action.

        - **list, retrieve, mine, subscribed** → Authenticated users.
        - **create, update, partial_update, destroy** → Journalists only.
        - **approve** → Editors only.
        """
        if self.action in ["list", "retrieve", "mine", "subscribed"]:
            return [permissions.IsAuthenticated()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsJournalist()]
        if self.action == "approve":
            return [IsEditor()]
        return super().get_permissions()

    def get_queryset(self):
        """
        Return a filtered queryset based on the user's role.

        - Anonymous users: only approved articles.
        - Staff/superusers: all articles.
        - Editors: all articles.
        - Journalists: own articles + approved ones.
        - Readers: only approved articles.
        """
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
        """
        Create a new article authored by the current user.

        Ensures only journalists (or staff/superusers) can create.
        New articles are saved with status ``PENDING``.

        Raises
        ------
        PermissionDenied
            If the user is not allowed to create articles.
        """
        u = self.request.user
        if not (hasattr(u, "is_journalist") and u.is_journalist()) and not (u.is_staff or u.is_superuser):
            raise PermissionDenied("Only journalists can create articles.")
        serializer.save(author=u, status=Article.Status.PENDING)

    def perform_update(self, serializer):
        """
        Update an article with role-based restrictions.

        - Editors: can update any article.
        - Journalists: can update only their own articles.
        - Staff/superusers: unrestricted.

        Raises
        ------
        PermissionDenied
            If the user is not allowed to update the article.
        """
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
        """
        Delete an article with role-based restrictions.

        - Editors: can delete any article.
        - Journalists: can delete only their own articles.
        - Staff/superusers: unrestricted.

        Raises
        ------
        PermissionDenied
            If the user is not allowed to delete the article.
        """
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
        """
        Approve an article.

        Changes status to APPROVED and sets ``approved_at`` timestamp if needed.

        Returns
        -------
        Response
            JSON with ``status`` and ``approved_at`` timestamp.
        """
        article = self.get_object()
        if article.status != Article.Status.APPROVED:
            article.status = Article.Status.APPROVED
            if not article.approved_at:
                article.approved_at = timezone.now()
            article.save(update_fields=["status", "approved_at"])
            return Response(
                {"status": "approved", "approved_at": article.approved_at},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"status": "already_approved", "approved_at": article.approved_at},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def mine(self, request):
        """
        List articles authored by the current journalist.

        Only returns results for journalist users.
        Results are ordered by newest first.
        """
        u = request.user
        qs = self.get_queryset().filter(author=u) if hasattr(
            u, "is_journalist") and u.is_journalist() else Article.objects.none()
        page = self.paginate_queryset(qs.order_by("-created_at"))
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def subscribed(self, request):
        """
        List approved articles from a reader's subscriptions.

        Includes articles from:
        - Publishers the reader is subscribed to.
        - Journalists the reader is subscribed to.

        Returns
        -------
        Response
            JSON list of approved subscribed articles.
        """
        u = request.user
        qs = Article.objects.filter(status=Article.Status.APPROVED)
        if hasattr(u, "is_reader") and u.is_reader():
            qs = qs.filter(
                Q(publisher__in=u.subscriptions_to_publishers.all())
                | Q(author__in=u.subscriptions_to_journalists.all())
            ).distinct()
        else:
            qs = Article.objects.none()
        qs = qs.order_by("-approved_at", "-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for :class:`~newsroom.models.Publisher`.

    Attributes
    ----------
    queryset : QuerySet
        All publishers.
    serializer_class : PublisherSerializer
        Serializer used for publishers.
    permission_classes : list
        Requires authentication.
    """

    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticated]
