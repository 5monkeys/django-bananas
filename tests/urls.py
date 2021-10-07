from django.urls import include, re_path

from bananas import admin
from bananas.admin import api

from . import separate_api
from .admin_api import FooAPI, HamAPI
from .drf import fenced_api

urlpatterns = [re_path(r"^admin/", admin.site.urls)]


api.register(FooAPI)
api.register(HamAPI)

urlpatterns += [
    re_path(r"^api/bananas", include("bananas.admin.api.urls")),
    re_path(r"^api/separate", include(separate_api)),
    re_path(r"^api/", include(fenced_api)),
]
