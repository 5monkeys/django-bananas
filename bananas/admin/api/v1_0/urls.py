from django.conf.urls import include, url

from .. import views
from ..router import register, router

register(views.LoginAPI)
register(views.LogoutAPI)
register(views.ChangePasswordAPI)

urlpatterns = [
    url(r"^schema.json", router.APISchemaView.as_view(router)),
    url(r"^", include(router.urls)),
]
