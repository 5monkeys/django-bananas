from django.conf.urls import include, url

from .router import router
from .versioning import __version__
from .views import AuthenticationAPIView

router.register(r"", AuthenticationAPIView, basename="auth")

urlpatterns = [
    url(
        r"^{version}/".format(version=__version__),
        include((router.urls, "bananas"), namespace=__version__),
    )
]
