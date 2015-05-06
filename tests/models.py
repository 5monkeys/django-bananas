from django.db import models
from django.db.models.manager import Manager

from bananas.models import TimeStampedModel, URLSecretField, SecretField,\
    UUIDModel
from bananas.query import ExtendedQuerySet


class Parent(TimeStampedModel):
    name = models.CharField(max_length=255)
    objects = Manager.from_queryset(ExtendedQuerySet)()


class Child(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Parent, null=True)
    objects = Manager.from_queryset(ExtendedQuerySet)()


class TestUUIDModel(UUIDModel):
    text = models.CharField(max_length=255)
    parent = models.ForeignKey('TestUUIDModel', null=True)


class SecretModel(models.Model):
    secret = SecretField()


class URLSecretModel(models.Model):
    # num_bytes=25 forces the base64 algorithm to pad
    secret = URLSecretField(num_bytes=25)
