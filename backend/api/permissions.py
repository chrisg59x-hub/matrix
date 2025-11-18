from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsManagerForWrites(BasePermission):
    """Read for any authenticated user; write only for managers/admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        u = getattr(request, "user", None)
        return bool(
            u
            and u.is_authenticated
            and getattr(u, "biz_role", "") in ("manager", "admin")
        )


class IsManagerOnly(BasePermission):
    """
    ANY method (including GET) requires manager/admin.
    No access for normal employees.
    """

    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        return bool(
            u
            and u.is_authenticated
            and getattr(u, "biz_role", "") in ("manager", "admin")
        )