from rest_framework.permissions import BasePermission


class IsAnonymous(BasePermission):
    """
    Allows access only to non-authenticated users.
    """

    def has_permission(self, request, view):
        return not request.user or request.user.is_anonymous
