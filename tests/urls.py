import django
from django.conf.urls import include, re_path

from bananas import admin

urlpatterns = [re_path(r"^admin/", admin.site.urls)]

if django.VERSION >= (1, 10):
    from bananas.admin import api
    from .admin_api import FooAPI, HamAPI
    from . import separate_api

    api.register(FooAPI)
    api.register(HamAPI)

    urlpatterns += [
        re_path(r"^api/bananas", include("bananas.admin.api.urls")),
        re_path(r"^api/separate", include(separate_api)),
    ]
