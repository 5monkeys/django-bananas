import django
from django.conf.urls import include, url

from bananas import admin

urlpatterns = [url(r"^admin/", admin.site.urls)]

if django.VERSION >= (1, 10):
    from bananas.admin import api
    from .admin_api import FooAPI, HamAPI

    api.register(FooAPI)
    api.register(HamAPI)

    urlpatterns += [url(r"^api/", include("bananas.admin.api.urls"))]
