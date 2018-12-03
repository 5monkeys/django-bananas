from rest_framework.versioning import URLPathVersioning

__version__ = "v1.0"


class BananasVersioning(URLPathVersioning):

    default_version = __version__
    allowed_versions = {__version__}
