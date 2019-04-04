from django.conf import settings
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import ugettext as _
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.inspectors.view import SwaggerAutoSchema
from drf_yasg.views import get_schema_view
from rest_framework import permissions, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.routers import SimpleRouter
from rest_framework.schemas.generators import is_custom_action
from rest_framework.versioning import URLPathVersioning

from ..versioning import BananasVersioning
from .base import BananasBaseRouter


class BananasOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        api_settings = getattr(settings, "ADMIN", {}).get("API", {})
        schema["schemes"] = api_settings.get("SCHEMES", schema["schemes"])
        return schema

    def get_paths(self, endpoints, components, request, public):
        paths, prefix = super().get_paths(endpoints, components, request, public)
        path = request._request.path
        return paths, path[: path.rfind("/")] + prefix


class BananasSwaggerSchema(SwaggerAutoSchema):
    def get_operation_id(self, operation_keys):
        name = ".".join(operation_keys[2:])
        meta = self.view.get_admin_meta()
        return meta.basename + ":" + name

    def get_summary_and_description(self):
        """
        Compat: drf-yasg 1.12+
        """
        summary = self.get_summary()
        _, description = super().get_summary_and_description()
        return summary, description

    def get_summary(self):
        """
        Compat: drf-yasg 1.11
        """
        title = None

        method_name = getattr(self.view, "action", self.method.lower())
        action = getattr(self.view, method_name, None)
        action_kwargs = getattr(action, "kwargs", None)

        if action_kwargs:
            title = action_kwargs.get("name")

        if not title and is_custom_action(self.view.action):
            title = _(self.view.action.replace("_", " ")).capitalize()

        if not title:
            meta = self.view.get_admin_meta()
            if self.view.action in ["retrieve", "update", "partial_update"]:
                title = str(meta.get("verbose_name") or meta.name)
            elif self.view.action == "create":
                title = meta.get("verbose_name")
                if title:
                    title = str(_("Add")) + " " + str(title).lower()
                else:
                    title = meta.name
            elif self.view.action == "list":
                title = str(meta.get("verbose_name_plural") or meta.name)
            else:
                title = str(meta.name)

        return title

    def get_tags(self, operation_keys):
        view = self.view
        meta = self.view.get_admin_meta()
        tags = ["app:{label}".format(label=meta.app_label)]

        if self.is_navigation():
            tags.append("navigation")

        if issubclass(view.__class__, viewsets.ModelViewSet):
            tags.append("crud")

        return [tag for tag in tags if tag not in meta.exclude_tags]

    def is_navigation(self):
        if not hasattr(self, "_is_navigation"):
            self._is_navigation = False
            try:
                if self.method == "GET" and (
                    self.view.action == "list" or not hasattr(self.view, "list")
                ):
                    self.view.reverse_action("list")
                    self._is_navigation = True
            except NoReverseMatch:
                pass

        return self._is_navigation


class BananasSimpleRouter(BananasBaseRouter, SimpleRouter):
    def get_schema_view(self):
        view = get_schema_view(
            openapi.Info(
                title="Django Bananas Admin API Schema",
                default_version=BananasVersioning.default_version,
                description="API for django-bananas.js",
                # terms_of_service="https://www.google.com/policies/terms/",
                # license=openapi.License(name="BSD License"),
            ),
            # validators=["flex", "ssv"],
            public=False,
            generator_class=BananasOpenAPISchemaGenerator,
            authentication_classes=(SessionAuthentication,),
            permission_classes=(permissions.AllowAny,),
            patterns=self.urls,
        )
        view.versioning_class = URLPathVersioning
        return view
