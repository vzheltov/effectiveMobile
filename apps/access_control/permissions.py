from rest_framework.permissions import BasePermission


class IsAccessAdmin(BasePermission):
    message = "Administrator role is required."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_active
            and request.user.user_roles.filter(role__code="admin").exists()
        )
