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

from ..versioning import BananasVersioning
from .base import BananasBaseRouter


class BananasOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_paths(self, endpoints, components, request, public):
        paths, prefix = super().get_paths(endpoints, components, request, public)
        path = request._request.path
        return paths, path[: path.rfind("/")]


class BananasSwaggerSchema(SwaggerAutoSchema):
    def get_operation_id(self, operation_keys):
        name = operation_keys[-1]
        meta = self.view.get_admin_meta()
        return meta.basename + ":" + name

    def get_summary(self):
        title = None

        method_name = getattr(self.view, "action", self.method.lower())
        action = getattr(self.view, method_name, None)
        action_kwargs = getattr(action, "kwargs", None)

        if action_kwargs:
            title = action_kwargs.get("name")

        if not title and is_custom_action(self.view.action):
            title = _(self.view.action.replace("_", " ")).capitalize()

        if not title:
            if self.is_navigation():
                meta = self.view.get_admin_meta()
                title = str(meta.name)

        return title

    def get_tags(self, operation_keys):
        view = self.view
        meta = self.view.get_admin_meta()
        tags = ["app:{label}".format(label=meta.app_label)]

        if meta.navigation is not False and self.is_navigation():
            tags.append("navigation")

        # if is_custom_action(view.action):
            # tags.append("action")
        # else:
            # operation = operation_keys[-1]
            # tags.append(operation)
        if issubclass(view.__class__, viewsets.ModelViewSet):
            tags.append("crud")

        return tags

    def is_navigation(self):
        if not hasattr(self, "_is_navigation"):
            self._is_navigation = False
            try:
                if self.view.action == "list" or not hasattr(self.view, "list"):
                    self.view.reverse_action("list")
                    self._is_navigation = True
            except NoReverseMatch:
                pass

        return self._is_navigation


class BananasSimpleRouter(BananasBaseRouter, SimpleRouter):
    def get_schema_view(self):
        return get_schema_view(
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
