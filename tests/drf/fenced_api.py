import operator

from django.urls import include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from bananas.drf.fencing import (
    FencedUpdateModelMixin,
    allow_if_match,
    allow_if_unmodified_since,
)
from tests.models import Parent


class SimpleSerializer(ModelSerializer):
    class Meta:
        model = Parent
        fields = ("name",)


class AllowIfUnmodifiedSinceAPI(FencedUpdateModelMixin, GenericViewSet):
    fence = allow_if_unmodified_since()
    serializer_class = SimpleSerializer
    queryset = Parent.objects.all()


class AllowIfMatchAPI(FencedUpdateModelMixin, GenericViewSet):
    fence = allow_if_match(operator.attrgetter("version"))
    serializer_class = SimpleSerializer

    def get_queryset(self):
        return Parent.objects.all()


router = DefaultRouter()
router.register(r"if-unmodified", AllowIfUnmodifiedSinceAPI, "if-unmodified")
router.register(r"if-match", AllowIfMatchAPI, "if-match")

urlpatterns = [re_path("fenced", include(router.urls))]
