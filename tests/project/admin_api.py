from typing import Any

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from bananas.admin.api.mixins import BananasAPI
from bananas.admin.api.schemas.decorators import tags
from bananas.admin.api.views import BananasAdminAPI
from bananas.lazy import lazy_capitalize, lazy_title


class HamSerializer(serializers.Serializer):
    spam = serializers.CharField()


class FooAPI(BananasAdminAPI):

    name = lazy_title(_("foo"))
    serializer_class = HamSerializer

    def list(self, request: Request) -> Response:
        serializer = self.serializer_class({"spam": "Skinka"})
        return Response(serializer.data)

    @action(detail=False)
    def bar(self, request: Request) -> Response:
        return Response({"bar": True})

    @tags(include=["navigation"])
    @action(detail=False, methods=["get", "post"])
    def baz(self, request: Request) -> Response:
        return Response({"baz": True})


class HamAPI(BananasAPI, viewsets.ModelViewSet):

    name = lazy_capitalize(_("ham"))
    serializer_class = HamSerializer

    def get_queryset(self) -> QuerySet:
        return None  # type: ignore

    @tags(exclude=["navigation"])
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response()
