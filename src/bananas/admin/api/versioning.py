from types import ModuleType
from typing import ClassVar, Dict, Sequence

from rest_framework.request import Request
from rest_framework.versioning import NamespaceVersioning

from . import v1_0

__versions__ = [v1_0]


class BananasVersioning(NamespaceVersioning):
    default_version: str = v1_0.__version__
    allowed_versions: Sequence[str] = tuple(
        version.__version__ for version in __versions__
    )
    version_map: ClassVar[Dict[str, ModuleType]] = {
        version.__version__: version for version in __versions__
    }

    def get_versioned_viewname(self, viewname: str, request: Request) -> str:
        """
        Prefix viewname with full namespace bananas:vX.Y:
        """
        assert request.resolver_match is not None
        namespace = request.resolver_match.namespace
        if namespace:
            viewname = f"{namespace}:{viewname}"

        return viewname
