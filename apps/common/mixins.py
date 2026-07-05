class OrganizationScopedQuerysetMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated or not user.organization_id:
            return qs.none()
        return qs.filter(organization_id=user.organization_id)