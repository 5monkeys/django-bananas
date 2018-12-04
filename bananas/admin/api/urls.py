from django.conf.urls import include, url

from . import views
from .router import register, router
from .versioning import __version__

register(views.LoginAPI)
register(views.LogoutAPI)
register(views.ChangePasswordAPI)

urlpatterns = [
    url(
        r"^(?P<version>{version})/".format(version=__version__),
        include((router.urls, "bananas"), namespace=__version__),
    )
]
