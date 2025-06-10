from typing import ClassVar, List

from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from bananas.admin.i18n import RawTranslationCatalog

from .mixins import BananasAPI
from .permissions import IsAnonymous
from .schemas import schema
from .serializers import (
    AuthenticationSerializer,
    PasswordChangeSerializer,
    UserSerializer,
)

UNDEFINED = object()


class BananasAdminAPI(BananasAPI, viewsets.GenericViewSet):
    pass


class LoginAPI(BananasAdminAPI):
    name = _("Log in")  # type: ignore[assignment]
    basename = "login"
    permission_classes = (IsAnonymous,)
    serializer_class = AuthenticationSerializer  # Placeholder for schema

    class Admin:
        verbose_name_plural = None

    @schema(responses={200: UserSerializer})
    def create(self, request: Request) -> Response:
        """
        Log in django staff user
        """
        # TODO: Decorate api with sensitive post parameters as Django admin do?
        # from django.utils.decorators import method_decorator
        # from django.views.decorators.debug import sensitive_post_parameters
        # sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

        login_form = AuthenticationForm(request, data=request.data)

        if not login_form.is_valid():
            raise serializers.ValidationError(login_form.errors)

        auth_login(request, login_form.get_user())

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutAPI(BananasAPI, viewsets.ViewSet):
    name = _("Log out")  # type: ignore[assignment]
    basename = "logout"

    class Admin:
        verbose_name_plural = None

    @schema(responses={204: ""})
    def create(self, request: Request) -> Response:
        """
        Log out django staff user
        """
        auth_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeAPI(BananasAdminAPI):
    serializer_class = UserSerializer

    class Admin:
        exclude_tags: ClassVar[List[str]] = ["navigation"]

    @schema(responses={200: UserSerializer})
    def list(self, request: Request) -> Response:
        """
        Retrieve logged in user info
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordAPI(BananasAdminAPI):
    name = _("Change password")  # type: ignore[assignment]
    basename = "change_password"
    serializer_class = PasswordChangeSerializer  # Placeholder for schema

    class Admin:
        verbose_name_plural = None

    @schema(responses={204: ""})
    def create(self, request: Request) -> Response:
        """
        Change password for logged in django staff user
        """
        # TODO: Decorate api with sensitive post parameters as Django admin do?

        assert isinstance(request.user, AbstractBaseUser)
        password_form = PasswordChangeForm(request.user, data=request.data)

        if not password_form.is_valid():
            raise serializers.ValidationError(password_form.errors)

        password_form.save()
        update_session_auth_hash(request, password_form.user)

        return Response(status=status.HTTP_204_NO_CONTENT)


class TranslationAPI(BananasAdminAPI):
    name = _("Translation catalog")  # type: ignore[assignment]
    basename = "i18n"
    permission_classes = (AllowAny,)

    class Admin:
        exclude_tags: ClassVar[List[str]] = ["navigation"]

    @schema(responses={200: ""})
    def list(self, request: Request) -> Response:
        """
        Retrieve the translation catalog.
        """
        return Response(RawTranslationCatalog().get(request))
