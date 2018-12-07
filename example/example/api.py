from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from bananas.admin.api.views import BananasAPI
from bananas.compat import reverse
from bananas.lazy import lazy_title


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("url", "username", "email", "is_staff")

    def build_url_field(self, field_name, model_class):
        """
        This is needed due to DRF's model serializer uses the queryset to build url name

        # TODO: Move this to own serializer mixin or fix problem elsewhere?
        """
        field, kwargs = super().build_url_field(field_name, model_class)

        view = self.root.context["view"]
        kwargs["view_name"] = view.get_url_name("detail")

        return field, kwargs


class UserViewSet(BananasAPI, viewsets.ModelViewSet):

    name = lazy_title(_("users"))
    permission_classes = (DjangoModelPermissions,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False)
    def foo(self, request):
        return Response("Just a simple extra list action")

    @action(detail=True)
    def bar(self, request, pk):
        url = reverse(
            "bananas:v1.0:example.user-bar",
            kwargs={"pk": pk},
        )
        return Response(f"Just a simple extra detail action, url = {url}")

    @action(detail=True, methods=["post"], name=_("Send activation e-mail"))
    def send_activation_email(self, request, pk):
        return Response(f"Just another simple extra detail action")
