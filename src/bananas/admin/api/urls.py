from django.urls import include, re_path

from .versioning import __versions__

apipatterns = [
    re_path(
        r"^{version}/".format(version=version.__version__),
        include(
            ("{package}.urls".format(package=version.__name__), "bananas"),
            namespace=version.__version__,
        ),
    )
    for version in __versions__
]


urlpatterns = [re_path(r"^", include((apipatterns, "bananas"), namespace="bananas"))]
