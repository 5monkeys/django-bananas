from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from bananas.admin.api.views import BananasAdminAPI


class HamSerializer(serializers.Serializer):
    spam = serializers.CharField()


class FooAPI(BananasAdminAPI):

    serializer_class = HamSerializer

    def list(self, request):
        serializer = self.serializer_class(dict(spam="Skinka"))
        return Response(serializer.data)

    @action(detail=False)
    def bar(self, request):
        return Response({"bar": "baz"})
