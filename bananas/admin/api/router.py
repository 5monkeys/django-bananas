from rest_framework.routers import SimpleRouter

from .views import BananasAPI

__all__ = ["register"]


class BananasRouter(SimpleRouter):

    def get_default_basename(self, viewset):
        return viewset.get_admin_meta().basename


def register(view: BananasAPI):
    meta = view.get_admin_meta()
    prefix = meta.basename.replace(".", "/")
    router.register(prefix, view, basename=meta.basename)


router = BananasRouter()
