from django.conf.urls import include, url

from .versioning import __versions__

apipatterns = [
    url(
        r"^{version}/".format(version=version.__version__),
        include(
            ("{package}.urls".format(package=version.__name__), "bananas"),
            namespace=version.__version__,
        ),
    )
    for version in __versions__
]


urlpatterns = [url(r"^", include((apipatterns, "bananas"), namespace="bananas"))]
