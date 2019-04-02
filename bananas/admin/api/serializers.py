from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import password_validators_help_texts
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from bananas.admin.api.schemas import schema_serializer_method


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="get_username", read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    is_superuser = serializers.BooleanField(read_only=True)
    permissions = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        ref_name = "Me"
        fields = (
            "id",
            "username",
            "full_name",
            "email",
            "is_superuser",
            "permissions",
            "groups",
        )
        read_only_fields = fields

    @schema_serializer_method(
        serializer_or_field=serializers.CharField(
            help_text=_("Falls back to username, if not implemented or empty")
        )
    )
    def get_full_name(self, obj):
        full_name = getattr(obj, "get_full_name", None)
        if full_name is not None:
            full_name = full_name()

        if not full_name:
            full_name = obj.get_username()

        return full_name

    @schema_serializer_method(
        serializer_or_field=serializers.CharField()
    )
    def get_email(self, obj):
        return getattr(obj, obj.get_email_field_name(), None)

    @schema_serializer_method(
        serializer_or_field=serializers.ListField(
            help_text=_(
                "Permissions that the user has, both through group and user permissions."
            )
        )
    )
    def get_permissions(self, obj):
        return sorted(obj.get_all_permissions())

    @schema_serializer_method(serializer_or_field=serializers.ListField)
    def get_groups(self, obj):
        return obj.groups.order_by("name").values_list("name", flat=True)


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
