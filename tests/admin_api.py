from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bananas.admin.api.mixins import BananasAPI
from bananas.admin.api.views import BananasAdminAPI
from bananas.lazy import lazy_capitalize, lazy_title


class HamSerializer(serializers.Serializer):
    spam = serializers.CharField()


class FooAPI(BananasAdminAPI):

    name = lazy_title(_("foo"))
    serializer_class = HamSerializer

    def list(self, request):
        serializer = self.serializer_class(dict(spam="Skinka"))
        return Response(serializer.data)

    @action(detail=False)
    def bar(self, request):
        return Response({"bar": "baz"})


class HamAPI(BananasAPI, viewsets.ModelViewSet):

    name = lazy_capitalize(_("ham"))
    serializer_class = HamSerializer

    def list(self, request):
        pass
