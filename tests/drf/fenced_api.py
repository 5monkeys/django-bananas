from django.urls import include, re_path
from rest_framework.mixins import UpdateModelMixin
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from tests.models import Parent

from bananas.drf.fencing import FencedUpdateModelMixin, allow_if_unmodified_since


class SimpleSerializer(ModelSerializer):
    class Meta:
        model = Parent
        fields = ("name",)


class FencedAPI(FencedUpdateModelMixin, UpdateModelMixin, GenericViewSet):
    fence = allow_if_unmodified_since
    serializer_class = SimpleSerializer

    def get_queryset(self):
        return Parent.objects.all()


router = DefaultRouter()
router.register(r"fenced", FencedAPI, "fenced")

urlpatterns = [re_path("", include(router.urls))]
