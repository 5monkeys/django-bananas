from django.urls import include, re_path

from .versioning import __versions__

apipatterns = [
    re_path(
        rf"^{version.__version__}/",
        include(
            (f"{version.__name__}.urls", "bananas"),
            namespace=version.__version__,
        ),
    )
    for version in __versions__
]


urlpatterns = [re_path(r"^", include((apipatterns, "bananas"), namespace="bananas"))]
