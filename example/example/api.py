from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, viewsets
from rest_framework.permissions import DjangoModelPermissions

from bananas.admin.api.views import BananasAPI
from bananas.lazy import lazy_title


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("url", "username", "email", "is_staff")

    def build_url_field(self, field_name, model_class):
        """
        This is needed due to DRF's model serializer uses the queryset to build url name

        # TODO: Move this to own HyperlinkedModelSerializer
        """
        field, kwargs = super().build_url_field(field_name, model_class)

        view = self.root.context['view']
        kwargs['view_name'] = view.get_reverse_name('detail')

        return field, kwargs


class UserViewSet(BananasAPI, viewsets.ModelViewSet):

    name = lazy_title(_("users"))
    permission_classes = (DjangoModelPermissions,)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    class Admin:
        verbose_name = "User"
