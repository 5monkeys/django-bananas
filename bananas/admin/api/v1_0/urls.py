from django.conf.urls import include, url
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .. import views
from ..router import register, router

register(views.LoginAPI)
register(views.LogoutAPI)
register(views.ChangePasswordAPI)

# TODO: Move to schemas module
schema_view = get_schema_view(
    openapi.Info(
        title="Django Bananas Admin API Schema",
        default_version="v1.0",
        description="API for django-bananas.js",
        # terms_of_service="https://www.google.com/policies/terms/",
        # license=openapi.License(name="BSD License"),
    ),
    # validators=["flex", "ssv"],
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=router.urls,
)

urlpatterns = [
    # url(r"^schema.json$", router.APISchemaView.as_view(router)),
    url(r"^schema(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0)),
    url(r"^swagger/$", schema_view.with_ui("swagger", cache_timeout=0)),
    url(r"^", include(router.urls)),
]
