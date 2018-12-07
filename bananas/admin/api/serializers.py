from django.contrib.auth import password_validation
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class AuthenticationSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"), write_only=True)
    password = serializers.CharField(label=_("Password"), write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(label=_("Old password"), write_only=True)
    new_password1 = serializers.CharField(
        label=_("New password"),
        help_text=password_validation.password_validators_help_text_html(),
        write_only=True,
    )
    new_password2 = serializers.CharField(
        label=_("New password confirmation"), write_only=True
    )
