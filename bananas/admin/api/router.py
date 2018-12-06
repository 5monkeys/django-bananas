from collections import OrderedDict

from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import SchemaGenerator

from .renderers import NamespacedJSONOpenAPIRenderer
from .views import BananasAPI, BananasSchemaView, NavigationView

__all__ = ["register"]


class BananasRouter(DefaultRouter):

    include_root_view = True
    include_format_suffixes = True
    root_view_name = "navigation"
    default_schema_renderers = [BrowsableAPIRenderer, NamespacedJSONOpenAPIRenderer]
    APIRootView = NavigationView
    APISchemaView = BananasSchemaView
    SchemaGenerator = SchemaGenerator

    def get_default_basename(self, viewset):
        return viewset.get_admin_meta().basename

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


def register(view: BananasAPI):
    meta = view.get_admin_meta()
    prefix = meta.basename.replace(".", "/")
    router.register(prefix, view, basename=meta.basename)


router = BananasRouter()
