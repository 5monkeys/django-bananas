from itertools import groupby

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, status, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.schemas.views import SchemaView
from rest_framework.utils import formatting

from bananas.models import ModelDict

from .permissions import IsAnonymous
from .versioning import BananasVersioning

UNDEFINED = object()


class BananasAPI(object):

    versioning_class = BananasVersioning

    @classmethod
    def get_admin_meta(cls):
        meta = getattr(cls, "_admin_meta", None)

        if meta is None:
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


class NavigationView(views.APIView):

    name = "Django Bananas Admin API"
    description = "User specific navigation endpoints for Django Bananas Admin API."
    _ignore_model_permissions = True
    schema = None  # exclude from schema
    api_root_dict = None

    def has_permission(self, viewset):
        view = viewset()
        for permission in view.get_permissions():
            if not permission.has_permission(self.request, view):
                return False
        return True

    def get(self, request, *args, **kwargs):
        ret = []
        namespace = request.resolver_match.namespace

        for key, (viewset, url_name) in self.api_root_dict.items():
            if not self.has_permission(viewset):
                continue

            meta = viewset.get_admin_meta()

            # TODO: Fix proper map between module and version
            urlconf = "bananas.admin.api.{version}.urls".format(
                version=kwargs["version"].replace(".", "_")
            )

            try:
                ret.append(
                    {
                        "path": reverse(
                            url_name, format=kwargs.get("format", None), urlconf=urlconf
                        ),
                        "endpoint": reverse(
                            "{}:{}".format(namespace, url_name),
                            args=args,
                            kwargs=kwargs,
                            request=request,  # Make url absolute
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


class BananasSchemaView(SchemaView):

    name = "{} Schema".format(NavigationView.name)

    @classmethod
    def as_view(cls, router):
        generator = router.SchemaGenerator(
            title=NavigationView.name,
            description="API for django-bananas.js",
            patterns=router.urls,
        )

        return super().as_view(
            renderer_classes=router.default_schema_renderers,
            schema_generator=generator,
            public=False,
            # authentication_classes=authentication_classes,
            # permission_classes=permission_classes,
        )


class BananasAPIViewSet(BananasAPI, viewsets.ViewSet):
    pass


class LoginAPI(BananasAPIViewSet):

    name = _("Log in")
    basename = "login"
    permission_classes = (IsAnonymous,)

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

    name = _("Log out")
    basename = "logout"
    permission_classes = (IsAuthenticated,)

    class Admin:
        verbose_name_plural = None

    def create(self, request):
        auth_logout(request)
        return Response(status=status.HTTP_202_ACCEPTED)


class ChangePasswordAPI(BananasAPIViewSet):

    name = _("Change password")
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
