from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ViewSet


class SomeThingAPI(ViewSet):
    def list(self, request):
        pass


separate_router = DefaultRouter()
separate_router.register(r"some-thing", SomeThingAPI, "some-thing")

urlpatterns = [url("", include(separate_router.urls))]
