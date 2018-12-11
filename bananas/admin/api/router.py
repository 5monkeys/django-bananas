from .mixins import BananasAPI
from .schemas import BananasRouter

__all__ = ["register"]


def register(view: BananasAPI):
    meta = view.get_admin_meta()
    prefix = meta.basename.replace(".", "/")
    router.register(prefix, view, meta.basename)


router = BananasRouter()
