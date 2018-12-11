from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.utils import formatting

from bananas.models import ModelDict

from .permissions import IsAnonymous
from .schemas import BananasSchema, schema
from .serializers import (
    AuthenticationSerializer,
    PasswordChangeSerializer,
    UserSerializer,
)
from .versioning import BananasVersioning

UNDEFINED = object()


class BananasAPI(object):

    authentication_classes = (SessionAuthentication,)
    versioning_class = BananasVersioning
    swagger_schema = BananasSchema  # for DRF: schema = BananasSchema()

    @classmethod
    def get_admin_meta(cls):
        meta = getattr(cls, "_admin_meta", None)

        if meta is None:
            # TODO: Get proper app_label, not only root package
            app_label, __, __ = cls.__module__.lower().partition(".")
            name = cls.get_view_name(cls)

            basename = getattr(cls, "basename", None)
            if basename is None:
                if type(name).__name__ == "__proxy__":
                    # name is lazy, probably gettext, extract basename from class name
                    basename = cls.get_view_name(cls, respect_name=False)
                else:
                    basename = name
                basename = basename.replace(" ", "_").lower()

            meta = ModelDict(
                app_label=app_label,
                basename=basename,
                name=name,
                # verbose_name=name,
                # verbose_name_plural=UNDEFINED,
            )

            admin = getattr(cls, "Admin", None)
            if admin is not None:
                meta.update(
                    {
                        key: getattr(admin, key)
                        for key in filter(
                            lambda key: key in meta, admin.__dict__.keys()
                        )
                    }
                )

            basename = "{}.{}".format(meta.app_label, meta.basename)
            # verbose_name_plural = (
            #     (meta.verbose_name + "s")
            #     if meta.verbose_name_plural is UNDEFINED
            #     else None
            # )
            meta.update(
                dict(
                    basename=basename,
                    # verbose_name_plural=verbose_name_plural,
                )
            )
            cls._admin_meta = meta

        return meta

    def reverse_action(self, url_name, *args, **kwargs):
        """
        Extended DRF with fallback to requested namespace if request.version is missing
        """
        if self.request and not self.request.version:
            return reverse(self.get_url_name(url_name), *args, **kwargs)

        return super().reverse_action(url_name, *args, **kwargs)

    def get_url_name(self, action_url_name="list"):
        """
        Get full namespaced url name to use for reverse()
        """
        url_name = "{}-{}".format(self.basename, action_url_name)

        namespace = self.request.resolver_match.namespace
        if namespace:
            url_name = "{}:{}".format(namespace, url_name)

        return url_name

    def get_view_name(self, respect_name=True):
        """
        Get or generate human readable view name.
        Extended version from DRF to support usage from both class and instance.
        """
        if isinstance(self, type):
            view = self
        else:
            view = self.__class__

        # Name may be set by some Views, such as a ViewSet.
        if respect_name:
            name = getattr(view, "name", None)
            if name is not None:
                return name

        name = view.__name__
        for suffix in ("View", "ViewSet", "API", "ApiView"):
            name = formatting.remove_trailing_string(name, suffix)
        name = formatting.camelcase_to_spaces(name)

        # Suffix may be set by some Views, such as a ViewSet.
        suffix = getattr(view, "suffix", None)
        if suffix:
            name += " " + suffix

        return name


class LoginAPI(BananasAPI, viewsets.GenericViewSet):

    name = _("Log in")
    basename = "login"
    permission_classes = (IsAnonymous,)
    serializer_class = AuthenticationSerializer  # Placeholder for schema

    class Admin:
        verbose_name_plural = None

    @schema(responses={200: UserSerializer})
    def create(self, request):
        # TODO: Decorate api with sensitive post parameters as Django admin do?
        # from django.utils.decorators import method_decorator
        # from django.views.decorators.debug import sensitive_post_parameters
        # sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

        login_form = AuthenticationForm(request, data=request.data)

        if not login_form.is_valid():
            raise serializers.ValidationError(login_form.errors)

        auth_login(request, login_form.get_user())

        # TODO: Return user?
        return Response(status=status.HTTP_200_OK)


class LogoutAPI(BananasAPI, viewsets.ViewSet):

    name = _("Log out")
    basename = "logout"
    permission_classes = (IsAuthenticated,)

    class Admin:
        verbose_name_plural = None

    @schema(responses={204: ""})
    def create(self, request):
        auth_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordAPI(BananasAPI, viewsets.GenericViewSet):

    name = _("Change password")
    basename = "change_password"
    permission_classes = (IsAuthenticated,)
    serializer_class = PasswordChangeSerializer  # Placeholder for schema

    class Admin:
        verbose_name_plural = None

    @schema(responses={204: ""})
    def create(self, request):
        # TODO: Decorate api with sensitive post parameters as Django admin do?

        password_form = PasswordChangeForm(request.user, data=request.data)

        if not password_form.is_valid():
            raise serializers.ValidationError(password_form.errors)

        password_form.save()

        return Response(status=status.HTTP_204_ACCEPTED)
