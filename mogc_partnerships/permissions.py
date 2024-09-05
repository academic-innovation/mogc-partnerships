from rest_framework.permissions import BasePermission

from .lib import get_cohort


class ManagerCreatePermission(BasePermission):
    managed_methods = "POST"

    def has_permission(self, request, view):
        if request.method not in self.managed_methods:
            return True

        user = request.user
        serializer = view.get_serializer(data=request.data)
        if not serializer.is_valid():
            return False

        partner = serializer.validated_data["partner"]
        if user in partner.managers.all():
            return True

        return False


class ManagerEditPermission(BasePermission):
    managed_methods = ("PUT", "PATCH")

    def has_permission(self, request, view):
        if request.method not in self.managed_methods:
            return True

        user = request.user
        cohort = get_cohort(request.user, view.kwargs.get("cohort_uuid"))
        partner = cohort.partner
        if user in partner.managers.all():
            return True

        return False
