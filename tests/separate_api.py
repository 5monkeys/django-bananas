from django.urls import include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ViewSet


class SomeThingAPI(ViewSet):
    def list(self, request):
        pass


separate_router = DefaultRouter()
separate_router.register(r"some-thing", SomeThingAPI, "some-thing")

urlpatterns = [re_path("", include(separate_router.urls))]
