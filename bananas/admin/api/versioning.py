from rest_framework.versioning import NamespaceVersioning

from . import v1_0

__versions__ = [v1_0]


class BananasVersioning(NamespaceVersioning):

    default_version = v1_0.__version__
    allowed_versions = {version.__version__ for version in __versions__}
    version_map = {version.__version__: version for version in __versions__}

    def get_versioned_viewname(self, viewname, request):
        """
        Prefix viewname with full namespace bananas:vX.Y:
        """
        namespace = request.resolver_match.namespace
        if namespace:
            viewname = "{}:{}".format(namespace, viewname)

        return viewname
