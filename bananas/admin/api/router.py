from .schemas import BananasRouter
from .views import BananasAPI

__all__ = ["register"]


def register(view: BananasAPI):
    meta = view.get_admin_meta()
    prefix = meta.basename.replace(".", "/")
    router.register(prefix, view, basename=meta.basename)


router = BananasRouter()
