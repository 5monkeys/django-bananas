from django.urls.exceptions import NoReverseMatch
from django.utils.translation import ugettext as _
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.inspectors.view import SwaggerAutoSchema
from rest_framework import viewsets
from rest_framework.schemas.generators import is_custom_action
from rest_framework.schemas.inspectors import AutoSchema
from rest_framework.schemas.views import SchemaView


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


class BananasOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def determine_path_prefix(self, paths):
        return "/api/v1.0"


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
        operation = operation_keys[-1]

        view = self.view
        meta = self.view.get_admin_meta()
        tags = ["app:{label}".format(label=meta.app_label)]

        if self.is_navigation():
            tags.append("navigation")

        if is_custom_action(view.action):
            tags.append("action")
        else:
            tags.append(operation)
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


class BananasSchemaView(SchemaView):

    name = "Django Bananas Admin API Schema"

    @classmethod
    def as_view(cls, router):
        generator = router.SchemaGenerator(
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
