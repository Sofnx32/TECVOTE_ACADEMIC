from rest_framework.permissions import BasePermission


class IsElectionManager(BasePermission):
    """
    Only ADMIN or ELECTORAL_COMMISSION can execute lifecycle actions.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role in {"ADMIN", "ELECTORAL_COMMISSION"}
        )