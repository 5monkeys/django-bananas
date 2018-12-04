from itertools import groupby

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.urls.exceptions import NoReverseMatch
from rest_framework import serializers, status, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from bananas.models import ModelDict

from .permissions import IsAnonymous
from .versioning import BananasVersioning

UNDEFINED = object()


class BananasAPI(object):

    versioning_class = BananasVersioning

    def get_reverse_name(self, url_name="list"):
        name = "{}-{}".format(self.basename, url_name)

        namespace = self.request.resolver_match.namespace
        if namespace:
            name = "{}:{}".format(namespace, name)

        return name

    @classmethod
    def get_admin_meta(cls):
        meta = getattr(cls, "_admin_meta", None)

        if meta is None:
            app_label, __, __ = cls.__module__.lower().partition(".")

            name = getattr(cls, "name", None)
            if name is None:
                name = cls().get_view_name()

            basename = getattr(cls, "basename", cls.__name__.lower())

            meta = ModelDict(
                app_label=app_label,
                name=name,
                basename=basename,
                prefix=None,
                verbose_name=name,
                verbose_name_plural=UNDEFINED,
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
            prefix = meta.prefix or basename.replace(".", "/")
            verbose_name_plural = (
                (meta.verbose_name + "s")
                if meta.verbose_name_plural is UNDEFINED
                else None
            )
            meta.update(
                dict(
                    basename=basename,
                    prefix=prefix,
                    verbose_name_plural=verbose_name_plural,
                )
            )
            cls._admin_meta = meta

        return meta


class BananasAPIViewSet(BananasAPI, viewsets.ViewSet):
    pass


class NavigationAPIView(views.APIView):
    """
    The root view for DefaultRouter
    """

    _ignore_model_permissions = True
    schema = None  # exclude from schema
    api_root_dict = None

    def get(self, request, *args, **kwargs):
        ret = []
        namespace = request.resolver_match.namespace

        for key, (meta, url_name) in self.api_root_dict.items():
            if namespace:
                url_name = namespace + ":" + url_name
            print(url_name)
            try:
                ret.append(
                    {
                        "endpoint": reverse(
                            url_name,
                            args=args,
                            kwargs=kwargs,
                            request=request,
                            format=kwargs.get("format", None),
                        ),
                        **meta,
                    }
                )
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                continue

        # Sort and group by app_label
        grouper = lambda item: item["app_label"]
        ret = {
            app_label: sorted(items, key=lambda item: item["name"])
            for app_label, items in groupby(sorted(ret, key=grouper), grouper)
        }

        return Response(ret)


class LoginAPI(BananasAPIViewSet):

    name = "Login"
    basename = "login"
    permission_classes = (IsAuthenticated,)

    class Admin:
        verbose_name_plural = None

    def create(self, request):
        """
        # TODO: Decorate api with sensitive post parameters as Django admin do?
        # from django.utils.decorators import method_decorator
        # from django.views.decorators.debug import sensitive_post_parameters
        # sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())
        """
        login_form = AuthenticationForm(request, data=request.data)

        if not login_form.is_valid():
            raise serializers.ValidationError(login_form.errors)

        auth_login(request, login_form.get_user())

        # TODO: Return user?
        return Response(status=status.HTTP_200_OK)


class LogoutAPI(BananasAPIViewSet):

    name = "Logout"
    basename = "logout"
    permission_classes = (IsAnonymous,)

    class Admin:
        verbose_name_plural = None

    def list(self, request):
        return self.create(request)

    def create(self, request):
        auth_logout(request)
        return Response(status=status.HTTP_202_ACCEPTED)


class ChangePasswordAPI(BananasAPIViewSet):

    name = "Change password"
    basename = "change_password"
    permission_classes = (IsAuthenticated,)

    class Admin:
        verbose_name_plural = None

    def create(self, request):
        password_form = PasswordChangeForm(request.user, data=request.data)

        if not password_form.is_valid():
            raise serializers.ValidationError(password_form.errors)

        password_form.save()

        return Response(status=status.HTTP_202_ACCEPTED)
