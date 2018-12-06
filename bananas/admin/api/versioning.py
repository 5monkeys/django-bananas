from rest_framework.versioning import NamespaceVersioning, URLPathVersioning

from . import v1_0

__versions__ = [v1_0]


# class BananasVersioning(URLPathVersioning):
class BananasVersioning(NamespaceVersioning):

    default_version = v1_0.__version__
    allowed_versions = {version.__version__ for version in __versions__}
