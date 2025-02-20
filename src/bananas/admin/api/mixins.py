from typing import TYPE_CHECKING, Any, Optional, Sequence, Type, TypeVar, cast

from django.db.models import Model
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.reverse import reverse
from rest_framework.utils import formatting
from rest_framework.versioning import BaseVersioning
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ViewSetMixin

from bananas.models import ModelDict

from .schemas import BananasSchema
from .versioning import BananasVersioning

if TYPE_CHECKING:
    from rest_framework.permissions import _PermissionClass
    from rest_framework.serializers import BaseSerializer

UNDEFINED = object()


class BananasAPI:
    versioning_class: Optional[Type[BaseVersioning]] = BananasVersioning
    authentication_classes: Sequence[Type[BaseAuthentication]] = (
        SessionAuthentication,
    )
    permission_classes: Sequence["_PermissionClass"] = (IsAdminUser,)
    swagger_schema = BananasSchema  # for DRF: schema = BananasSchema()

    _admin_meta: ModelDict
    basename: str

    @classmethod
    def get_admin_meta(cls) -> ModelDict:
        meta: Optional[ModelDict] = getattr(cls, "_admin_meta", None)

        if meta is None:
            # TODO: Get proper app_label, not only root package
            app_label, __, __ = cls.__module__.lower().partition(".")
            name = cls.get_view_name(cls)  # type: ignore[arg-type]

            basename = getattr(cls, "basename", None)
            if basename is None:
                if type(name).__name__ == "__proxy__":
                    # name is lazy, probably gettext, extract basename from class name
                    basename = cls.get_view_name(cls, respect_name=False)  # type: ignore[arg-type]
                else:
                    basename = name
                basename = basename.replace(" ", "_").lower()

            meta = ModelDict(
                app_label=app_label,
                basename=basename,
                name=name,
                exclude_tags=[],
                verbose_name=None,
                verbose_name_plural=name,
            )

            admin = getattr(cls, "Admin", None)
            if admin is not None:
                meta.update(
                    {
                        key: getattr(admin, key)
                        for key in filter(
                            lambda key: key in meta,
                            admin.__dict__.keys(),
                        )
                    }
                )

            basename = f"{meta.app_label}.{meta.basename}"
            meta.update({"basename": basename})
            cls._admin_meta = meta

        return meta

    def reverse_action(self, url_name: str, *args: Any, **kwargs: Any) -> str:
        """
        Extended DRF with fallback to requested namespace if request.version is missing
        """
        request = cast(APIView, self).request
        if request and not request.version:
            return reverse(self.get_url_name(url_name), *args, **kwargs)

        return cast(ViewSetMixin, super()).reverse_action(url_name, *args, **kwargs)

    def get_url_name(self, action_url_name: str = "list") -> str:
        """
        Get full namespaced url name to use for reverse()
        """
        url_name = f"{self.basename}-{action_url_name}"

        request = cast(APIView, self).request
        assert request.resolver_match
        namespace = request.resolver_match.namespace
        if namespace:
            url_name = f"{namespace}:{url_name}"

        return url_name

    def get_view_name(self, respect_name: bool = True) -> str:
        """
        Get or generate human readable view name.
        Extended version from DRF to support usage from both class and instance.
        """
        view: Type
        if isinstance(self, type):
            view = self
        else:
            view = self.__class__

        # Name may be set by some Views, such as a ViewSet.
        if respect_name:
            name: Optional[str] = getattr(view, "name", None)
            if name is not None:
                return name

        name = view.__name__
        for view_suffix in ("ViewSet", "View", "API", "Admin"):
            name = formatting.remove_trailing_string(name, view_suffix)
        name = formatting.camelcase_to_spaces(name)

        # Suffix may be set by some Views, such as a ViewSet.
        suffix: Optional[str] = getattr(view, "suffix", None)
        if suffix:
            name += " " + suffix

        return name


_MT_co = TypeVar("_MT_co", bound=Model, covariant=True)


class SchemaSerializerMixin:
    def get_serializer_class(self) -> Type["BaseSerializer[_MT_co]"]:
        serializer_class = cast(GenericViewSet, super()).get_serializer_class()

        action = getattr(self, cast(GenericViewSet, self).action, None)
        schema = getattr(action, "_swagger_auto_schema", None)
        if schema:
            responses = schema.get("responses")
            if responses:
                status_code = sorted(responses.keys())[0]
                if status_code < 300:
                    serializer_class = responses[status_code]

        return serializer_class
