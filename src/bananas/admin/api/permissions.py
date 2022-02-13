from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAnonymous(BasePermission):
    """
    Allows access only to non-authenticated users.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        return not request.user or request.user.is_anonymous
