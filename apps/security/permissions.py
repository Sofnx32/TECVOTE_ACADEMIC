from rest_framework.permissions import BasePermission

class IsSameOrganization(BasePermission):
    def has_object_permission(self, request, view, obj):
        user_org = getattr(request.user, "organization_id", None)
        obj_org = getattr(obj, "organization_id", None)
        return bool(user_org and obj_org and user_org == obj_org)