from .schemas import BananasRouter

__all__ = ["register"]


def register(view):  # Type[BananasAPI]
    """
    Register the API view class in the bananas router.

    :param BananasAPI view:
    """
    meta = view.get_admin_meta()
    prefix = meta.basename.replace(".", "/")
    router.register(prefix, view, meta.basename)


router = BananasRouter()
