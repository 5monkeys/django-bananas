from typing import TYPE_CHECKING, Type, TypeVar, cast

from rest_framework.viewsets import ViewSetMixin

from .schemas import BananasRouter

if TYPE_CHECKING:
    from .mixins import BananasAPI

__all__ = ["register"]


T = TypeVar("T", bound=ViewSetMixin)


def register(view: Type[T]) -> None:
    """
    Register the API view class in the bananas router.

    :param BananasAPI view:
    """
    meta = cast("BananasAPI", view).get_admin_meta()
    prefix = meta.basename.replace(".", "/")
    router.register(prefix, view, meta.basename)


router = BananasRouter()
