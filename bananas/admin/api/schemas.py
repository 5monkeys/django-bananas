from django.utils.translation import ugettext as _
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
