"""
Custom permission classes for the Newsroom API.

This module defines role-based and action-based permission classes
for use with Django REST Framework viewsets and views.

Helpers
-------
The helper functions (_is_auth, _is_admin, etc.) wrap role checks on
the custom User model, handling missing methods gracefully.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


# ---- Helpers ---------------------------------------------------------------

def _is_auth(u) -> bool:
    """
    Check if the user is authenticated.

    Parameters
    ----------
    u : User
        The user instance.

    Returns
    -------
    bool
        True if authenticated, else False.
    """
    return bool(u and u.is_authenticated)


def _is_admin(u) -> bool:
    """
    Check if the user is a staff or superuser.

    Parameters
    ----------
    u : User
        The user instance.

    Returns
    -------
    bool
        True if staff or superuser, else False.
    """
    return bool(getattr(u, "is_staff", False) or getattr(u, "is_superuser", False))


def _is_reader(u) -> bool:
    """
    Check if the user has the Reader role.

    Parameters
    ----------
    u : User
        The user instance.

    Returns
    -------
    bool
        True if Reader, else False.
    """
    try:
        return u.is_reader()
    except Exception:
        return False


def _is_editor(u) -> bool:
    """
    Check if the user has the Editor role.

    Parameters
    ----------
    u : User
        The user instance.

    Returns
    -------
    bool
        True if Editor, else False.
    """
    try:
        return u.is_editor()
    except Exception:
        return False


def _is_journalist(u) -> bool:
    """
    Check if the user has the Journalist role.

    Parameters
    ----------
    u : User
        The user instance.

    Returns
    -------
    bool
        True if Journalist, else False.
    """
    try:
        return u.is_journalist()
    except Exception:
        return False


# ---- Simple role gates (view-level) ---------------------------------------

class IsReader(BasePermission):
    """
    Allow only Readers (plus staff/superusers).
    """

    def has_permission(self, request, view):
        """
        Check if the user is a Reader or admin.
        """
        u = request.user
        return _is_auth(u) and (_is_reader(u) or _is_admin(u))


class IsEditor(BasePermission):
    """
    Allow only Editors (plus staff/superusers).
    """

    def has_permission(self, request, view):
        """
        Check if the user is an Editor or admin.
        """
        u = request.user
        return _is_auth(u) and (_is_editor(u) or _is_admin(u))


class IsJournalist(BasePermission):
    """
    Allow only Journalists (plus staff/superusers).
    """

    def has_permission(self, request, view):
        """
        Check if the user is a Journalist or admin.
        """
        u = request.user
        return _is_auth(u) and (_is_journalist(u) or _is_admin(u))


# ---- Read-only convenience -------------------------------------------------

class ReadOnly(BasePermission):
    """
    Allow only safe methods (GET/HEAD/OPTIONS).
    """

    def has_permission(self, request, view):
        """
        Check if the request method is safe.
        """
        return request.method in SAFE_METHODS


class IsEditorOrReadOnly(BasePermission):
    """
    Anyone can read; only Editors (or staff/superusers) can modify.
    """

    def has_permission(self, request, view):
        """
        Check read-only for all, write access for Editors/admins.
        """
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return _is_auth(u) and (_is_editor(u) or _is_admin(u))


class IsJournalistOrReadOnly(BasePermission):
    """
    Anyone can read; only Journalists (or staff/superusers) can modify.
    """

    def has_permission(self, request, view):
        """
        Check read-only for all, write access for Journalists/admins.
        """
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return _is_auth(u) and (_is_journalist(u) or _is_admin(u))


# ---- Object-level checks ---------------------------------------------------

class IsAuthorOrEditor(BasePermission):
    """
    SAFE methods are allowed.
    For write methods: allow if the user is the object's author,
    an Editor, or staff/superuser.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is author, Editor, or admin for unsafe methods.

        Parameters
        ----------
        obj : Model
            The object being accessed.

        Returns
        -------
        bool
            True if permission is granted, else False.
        """
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        is_author = (getattr(obj, "author_id", None) == getattr(u, "id", None))
        return _is_auth(u) and (is_author or _is_editor(u) or _is_admin(u))


# ---- Approval permission (optional, if you want to check the custom perm) --

class CanApprove(BasePermission):
    """
    Allow users who can approve (custom model perm) or Editors/admins.

    Notes
    -----
    The Article model defines::

        Meta.permissions = [("can_approve", "Can approve articles")]
    """

    def has_permission(self, request, view):
        """
        Check if user is allowed to approve articles.
        """
        u = request.user
        return _is_auth(u) and (
            _is_editor(u) or _is_admin(u) or u.has_perm("newsroom.can_approve")
        )
