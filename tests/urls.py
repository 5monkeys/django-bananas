from django.urls import include, re_path

from bananas import admin

from .utils import drf_installed

urlpatterns = [re_path(r"^admin/", admin.site.urls)]


if drf_installed():
    from bananas.admin import api

    from .drf import admin_api, fenced_api, separate_api

    api.register(admin_api.FooAPI)
    api.register(admin_api.HamAPI)
    urlpatterns += [
        re_path(r"^api/bananas", include("bananas.admin.api.urls")),
        re_path(r"^api/separate", include(separate_api)),
        re_path(r"^api/", include(fenced_api)),
    ]
