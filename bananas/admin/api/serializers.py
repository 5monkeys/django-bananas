from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import password_validators_help_texts
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from bananas.admin.api.schemas import schema_serializer_method


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="get_username", read_only=True)
    is_superuser = serializers.BooleanField()
    permissions = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    @schema_serializer_method(serializer_or_field=serializers.ListField)
    def get_permissions(self, obj):
        return sorted(obj.get_all_permissions())

    @schema_serializer_method(serializer_or_field=serializers.ListField)
    def get_groups(self, obj):
        return obj.groups.order_by("name").values_list("name", flat=True)

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "is_superuser", "permissions", "groups")
        read_only_fields = fields


class AuthenticationSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"), write_only=True)
    password = serializers.CharField(label=_("Password"), write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(label=_("Old password"), write_only=True)
    new_password1 = serializers.CharField(
        label=_("New password"),
        help_text=password_validators_help_texts(),
        write_only=True,
    )
    new_password2 = serializers.CharField(
        label=_("New password confirmation"), write_only=True
    )
