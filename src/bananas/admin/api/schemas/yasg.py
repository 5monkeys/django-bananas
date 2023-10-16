from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, cast

from django.conf import settings
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext as _
from drf_yasg import openapi
from drf_yasg.generators import EndpointEnumerator, OpenAPISchemaGenerator
from drf_yasg.inspectors.view import SwaggerAutoSchema
from drf_yasg.views import get_schema_view
from rest_framework import permissions, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request
from rest_framework.routers import SimpleRouter
from rest_framework.schemas.coreapi import is_custom_action

from bananas.admin.api.versioning import BananasVersioning

from .base import BananasBaseRouter


class BananasEndpointEnumerator(EndpointEnumerator):
    def should_include_endpoint(
        self,
        path: str,
        callback: Callable,
        app_name: str = "",
        namespace: str = "",
        url_name: Optional[str] = None,
    ) -> bool:
        # Fall back to check namespace on the resolver match
        request = self.request
        if (
            not namespace
            and getattr(request, "version", None)
            and getattr(request, "resolver_match", None)
        ):
            namespace = request.resolver_match.namespace or ""
        return cast(
            bool,
            super().should_include_endpoint(
                path, callback, app_name, namespace, url_name
            ),
        )


class BananasOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    endpoint_enumerator_class = BananasEndpointEnumerator

    def get_schema(
        self, request: Optional[Request] = None, public: bool = False
    ) -> Dict[str, Any]:
        schema: Dict[str, Any] = super().get_schema(request, public)
        api_settings = getattr(settings, "ADMIN", {}).get("API", {})
        schema["schemes"] = api_settings.get("SCHEMES", schema["schemes"])
        return schema

    def get_paths(
        self, endpoints: Dict[str, Any], components: Any, request: Request, public: bool
    ) -> Tuple[Any, str]:
        paths, prefix = super().get_paths(endpoints, components, request, public)
        path = request._request.path
        return paths, path[: path.rfind("/")] + prefix


class BananasSwaggerSchema(SwaggerAutoSchema):
    def get_operation_id(self, operation_keys: Sequence[str]) -> str:
        name = ".".join(operation_keys[2:])
        basename: str = self.view.get_admin_meta().basename
        return basename + ":" + name

    def get_summary_and_description(self) -> Tuple[Optional[str], str]:
        """
        Compat: drf-yasg 1.12+
        """
        summary = self.get_summary()
        _, description = super().get_summary_and_description()
        return summary, description

    def get_summary(self) -> str:
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

    def get_tags(self, operation_keys: Tuple[str, ...]) -> List[str]:
        view = self.view
        meta = self.view.get_admin_meta()
        tags = {f"app:{meta.app_label}"}

        if self.is_navigation():
            tags.add("navigation")

        if issubclass(view.__class__, viewsets.ModelViewSet):
            tags.add("crud")

        view_method = getattr(view, view.action, None)
        if view_method:
            include_tags = set(getattr(view_method, "include_tags", None) or [])
            exclude_tags = set(getattr(view_method, "exclude_tags", None) or [])
            tags |= include_tags
            tags -= exclude_tags

        return [tag for tag in tags if tag not in meta.exclude_tags]

    def is_navigation(self) -> bool:
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
    def get_schema_view(self) -> Any:
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
        view.versioning_class = BananasVersioning

        return view
