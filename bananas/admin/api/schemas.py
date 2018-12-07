from rest_framework.schemas.inspectors import AutoSchema
from rest_framework.schemas.views import SchemaView


class BananasSchema(AutoSchema):
    def get_link(self, *args, **kwargs):
        link = super().get_link(*args, **kwargs)
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
