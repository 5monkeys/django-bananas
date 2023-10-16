from typing import TYPE_CHECKING, Any, Type, cast

from rest_framework.viewsets import ViewSetMixin

if TYPE_CHECKING:
    from bananas.admin.api.mixins import BananasAPI


class BananasBaseRouter:
    def get_default_basename(self, viewset: Type[ViewSetMixin]) -> str:
        return cast(Type["BananasAPI"], viewset).get_admin_meta().basename  # type: ignore[no-any-return]

    def get_schema_view(self) -> Any:
        raise NotImplementedError
