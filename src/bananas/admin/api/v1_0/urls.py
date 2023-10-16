from django.urls import include, re_path

from bananas.admin.api import views
from bananas.admin.api.router import register, router

register(views.LoginAPI)
register(views.LogoutAPI)
register(views.MeAPI)
register(views.ChangePasswordAPI)
register(views.TranslationAPI)

schema_view = router.get_schema_view()

urlpatterns = [
    re_path(
        r"^schema(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema",
    ),
    re_path(
        r"^swagger$", schema_view.with_ui("swagger", cache_timeout=0), name="swagger"
    ),
    re_path(r"^$", schema_view.with_ui("redoc", cache_timeout=0), name="root"),
    re_path(r"^", include(router.urls)),
]
