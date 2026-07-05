from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsElectionManagerOrReadOnly(BasePermission):
    """
    Read: any authenticated user
    Write: ADMIN or ELECTORAL_COMMISSION
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return user.role in {"ADMIN", "ELECTORAL_COMMISSION"}