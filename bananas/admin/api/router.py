from rest_framework.routers import DefaultRouter

from .views import NavigationAPIView

__all__ = ["register"]


class BananasRouter(DefaultRouter):

    # include_root_view = True
    # include_format_suffixes = True
    root_view_name = 'navigation'
    # default_schema_renderers = None
    APIRootView = NavigationAPIView
    # APISchemaView = SchemaView
    # SchemaGenerator = SchemaGenerator


def register(*args, **kwargs):
    router.register(*args, **kwargs)


router = BananasRouter()
