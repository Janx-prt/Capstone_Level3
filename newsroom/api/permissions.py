# newsroom/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


# ---- Helpers ---------------------------------------------------------------

def _is_auth(u) -> bool:
    return bool(u and u.is_authenticated)


def _is_admin(u) -> bool:
    return bool(getattr(u, "is_staff", False) or getattr(u, "is_superuser", False))


def _is_reader(u) -> bool:
    try:
        return u.is_reader()
    except Exception:
        return False


def _is_editor(u) -> bool:
    try:
        return u.is_editor()
    except Exception:
        return False


def _is_journalist(u) -> bool:
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
        u = request.user
        return _is_auth(u) and (_is_reader(u) or _is_admin(u))


class IsEditor(BasePermission):
    """
    Allow only Editors (plus staff/superusers).
    """

    def has_permission(self, request, view):
        u = request.user
        return _is_auth(u) and (_is_editor(u) or _is_admin(u))


class IsJournalist(BasePermission):
    """
    Allow only Journalists (plus staff/superusers).
    """

    def has_permission(self, request, view):
        u = request.user
        return _is_auth(u) and (_is_journalist(u) or _is_admin(u))


# ---- Read-only convenience -------------------------------------------------

class ReadOnly(BasePermission):
    """
    Allow only safe (GET/HEAD/OPTIONS) methods.
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsEditorOrReadOnly(BasePermission):
    """
    Anyone can read; only Editors (or staff/superusers) can modify.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return _is_auth(u) and (_is_editor(u) or _is_admin(u))


class IsJournalistOrReadOnly(BasePermission):
    """
    Anyone can read; only Journalists (or staff/superusers) can modify.
    """

    def has_permission(self, request, view):
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
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        is_author = (getattr(obj, "author_id", None) == getattr(u, "id", None))
        return _is_auth(u) and (is_author or _is_editor(u) or _is_admin(u))


# ---- Approval permission (optional, if you want to check the custom perm) --

class CanApprove(BasePermission):
    """
    Allow users who can approve (custom model perm) or Editors/admins.
    Your Article model defines Meta.permissions = [("can_approve", "...")].
    """

    def has_permission(self, request, view):
        u = request.user
        return _is_auth(u) and (
            _is_editor(u) or _is_admin(u) or u.has_perm("newsroom.can_approve")
        )
