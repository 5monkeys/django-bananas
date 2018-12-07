from django.contrib.auth.password_validation import password_validators_help_texts
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


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
