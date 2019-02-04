from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from bananas.admin.api.schemas import schema, schema_serializer_method
from bananas.admin.api.views import BananasAPI
from bananas.compat import reverse
from bananas.lazy import lazy_title


class UserDetailsSerializer(serializers.HyperlinkedModelSerializer):
    full_name = serializers.SerializerMethodField()

    @schema_serializer_method(serializer_or_field=serializers.CharField)
    def get_full_name(self, obj):
        return obj.get_full_name()

    class Meta:
        model = User
        fields = ("id", "url", "username", "full_name", "email", "is_staff")

    def build_url_field(self, field_name, model_class):
        """
        This is needed due to DRF's model serializer uses the queryset to build url name

        # TODO: Move this to own serializer mixin or fix problem elsewhere?
        """
        field, kwargs = super().build_url_field(field_name, model_class)

        view = self.root.context["view"]
        kwargs["view_name"] = view.get_url_name("detail")

        return field, kwargs


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")


class UserFilterSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)


class UserViewSet(BananasAPI, viewsets.ModelViewSet):

    name = lazy_title(_("users"))
    permission_classes = (DjangoModelPermissions,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    class Admin:
        verbose_name = lazy_title(_("user"))

    @schema(query_serializer=UserFilterSerializer)
    def list(self, request):
        return super().list(request)

    def get_queryset(self):
        queryset = super().get_queryset()

        serializer = UserFilterSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get("username")
        if username:
            queryset = queryset.filter(username__contains=username)

        return queryset

    def get_serializer_class(self):
        if self.action in ("retrieve", "list"):
            return UserDetailsSerializer
        else:
            return UserSerializer

    @action(detail=False)
    def foo(self, request):
        return Response("Just a simple extra list action")

    @action(detail=True)
    def bar(self, request, pk):
        url = reverse("bananas:v1.0:example.user-bar", kwargs={"pk": pk})
        return Response(f"Just a simple extra detail action, url = {url}")

    @action(detail=True, methods=["post"], name=_("Send activation e-mail"))
    def send_activation_email(self, request, pk):
        return Response(f"Just another simple extra detail action")
