from django.urls import include, re_path
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ViewSet


class SomeThingAPI(ViewSet):
    def list(self, request: Request) -> Response:
        pass


separate_router = DefaultRouter()
separate_router.register(r"some-thing", SomeThingAPI, "some-thing")

urlpatterns = [re_path("", include(separate_router.urls))]
