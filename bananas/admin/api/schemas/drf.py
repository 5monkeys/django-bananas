"""
DRF 3.9.0 generator, schema, router, views etc.
TODO: Nuke when decided for yasg
"""
from collections import OrderedDict
from itertools import groupby

from django.urls.exceptions import NoReverseMatch
from django.utils.translation import ugettext_lazy as _
from rest_framework import renderers, views, viewsets
from rest_framework.compat import urlparse
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import SchemaGenerator
from rest_framework.schemas.generators import is_custom_action
from rest_framework.schemas.inspectors import AutoSchema
from rest_framework.schemas.views import SchemaView

from .base import BananasBaseRouter
from .versioning import BananasVersioning
from .views import BananasAPI


class BananasSchema(AutoSchema):
    def get_method(self, method):
        method_name = getattr(self.view, "action", method.lower())
        method = getattr(self.view, method_name, None)
        return method

    def get_title(self, path, method):
        title = None

        action = self.get_method(method)
        action_kwargs = getattr(action, "kwargs", None)

        if action_kwargs:
            title = action_kwargs.get("name")

        if not title and is_custom_action(self.view.action):
            title = _(self.view.action.replace("_", " ")).capitalize()

        return title

    def get_link(self, path, method, base_url):
        link = super().get_link(path, method, base_url)
        link._title = self.get_title(path, method)
        link._view = self.view  # Attach view instance for later use in renderer
        return link


class BananasSchemaView(SchemaView):

    name = "Django Bananas Admin API Schema"

    @classmethod
    def as_view(cls, router):
        generator = SchemaGenerator(
            title=cls.name,
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


class NavigationView(BananasAPI, views.APIView):

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
        urlconf = "{version_package}.urls".format(
            version_package=BananasVersioning.version_map[request.version].__name__
        )

        for key, (viewset, url_name) in self.api_root_dict.items():
            if not self.has_permission(viewset):
                continue

            meta = viewset.get_admin_meta()

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


class NamespacedJSONOpenAPIRenderer(renderers.JSONOpenAPIRenderer):
    def render(self, data, *args, **kwargs):
        """
        Render using DRF JSONRenderer to get extra features like indent and encoding
        """
        structure = self.get_structure(data)
        return renderers.JSONRenderer().render(structure, *args, **kwargs)

    def get_parameters(self, link):
        """
        Copy of DRF to support field.location "form"
        """
        parameters = []
        for field in link.fields:
            if field.location not in ["path", "query", "form"]:
                continue
            parameter = {"name": field.name, "in": field.location}
            if field.required:
                parameter["required"] = True
            if field.description:
                parameter["description"] = field.description
            if field.schema:
                parameter["schema"] = self.get_schema(field.schema)
            parameters.append(parameter)
        return parameters

    def get_operation(self, link, name, tag):
        operation = super().get_operation(link, name, tag)

        view = link._view  # FYI: Set in BananasSchema.get_link
        meta = view.get_admin_meta()

        operation["operationId"] = meta.basename + ":" + name
        operation["tags"] = ["app:{label}".format(label=meta.app_label)]

        try:
            is_navigation = False
            if name == "list" or not hasattr(view, "list"):
                view.reverse_action("list")
                is_navigation = True
        except NoReverseMatch:
            pass

        if is_navigation:
            operation["summary"] = str(meta.name)
            operation["tags"].append("navigation")

        if is_custom_action(view.action):
            operation["tags"].append("action")
        else:
            operation["tags"].append(name)
            if issubclass(view.__class__, viewsets.ModelViewSet):
                operation["tags"].append("crud")

        return operation

    def get_structure(self, data):
        structure = super().get_structure(data)
        structure["info"]["version"] = BananasVersioning.default_version
        return structure

    def get_paths(self, document):
        """
        Temporary fix to support namespace versioning.

        See: https://github.com/calvin620707/DRF-OpenApiRender-NestUrlPatterns/blob/master/demo/demo/urls.py

        # TODO: Remove when bug fixed in DRF
        """
        paths = {}

        tag = None
        for name, link in document.links.items():
            path = urlparse.urlparse(link.url).path
            method = link.action.lower()
            paths.setdefault(path, {})
            paths[path][method] = self.get_operation(link, name, tag=tag)

        for tag, section in document.data.items():
            if not section.links:
                sub_paths = self.get_paths(section)
                paths.update(sub_paths)
                continue

            for name, link in section.links.items():
                path = urlparse.urlparse(link.url).path
                method = link.action.lower()
                paths.setdefault(path, {})
                paths[path][method] = self.get_operation(link, name, tag=tag)

        return paths


class BananasRouter(BananasBaseRouter, DefaultRouter):

    include_root_view = True
    include_format_suffixes = True
    root_view_name = "navigation"
    default_schema_renderers = [BrowsableAPIRenderer, NamespacedJSONOpenAPIRenderer]
    APIRootView = NavigationView

    def get_schema_view(self):
        return BananasSchemaView.as_view(self)

    def get_api_root_view(self, api_urls=None):
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name

        for prefix, viewset, basename in self.registry:
            try:
                api_root_dict[prefix] = (viewset, list_name.format(basename=basename))
            except AttributeError:
                # TODO: log warning, extend bananas api
                continue

        return self.APIRootView.as_view(api_root_dict=api_root_dict)
