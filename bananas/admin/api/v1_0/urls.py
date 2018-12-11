from django.conf.urls import include, url

from .. import views
from ..router import register, router

register(views.LoginAPI)
register(views.LogoutAPI)
register(views.ChangePasswordAPI)

schema_view = router.get_schema_view()

urlpatterns = [
    url(r"^schema(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0)),
    url(r"^swagger$", schema_view.with_ui("swagger", cache_timeout=0)),
    url(r"^$", schema_view.with_ui("redoc", cache_timeout=0)),
    url(r"^", include(router.urls)),
]
