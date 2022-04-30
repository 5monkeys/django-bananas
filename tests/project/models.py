from typing import NoReturn

from django.db import models
from django.db.models import Model
from django.db.models.manager import Manager

from bananas.models import SecretField, TimeStampedModel, URLSecretField, UUIDModel
from bananas.query import ExtendedQuerySet, ModelDictManagerMixin


class SimpleManager(ModelDictManagerMixin, Manager):
    pass


class Simple(Model):
    name = models.CharField(max_length=255)
    objects = SimpleManager()


class Parent(TimeStampedModel):
    name = models.CharField(max_length=255)
    # TODO: django-stubs errors when `objects` gets a type that's not directly of
    #       `QuerySet`. Related: https://github.com/typeddjango/django-stubs/issues/905
    objects = Manager.from_queryset(ExtendedQuerySet)()  # type: ignore[django-manager]

    @property
    def attribute_error(self) -> NoReturn:
        raise AttributeError()

    @property
    def version(self) -> str:
        return str(self.pk) + ":" + str(self.date_modified)


class Child(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Parent, null=True, on_delete=models.CASCADE)
    objects = Manager.from_queryset(ExtendedQuerySet)()  # type: ignore[django-manager]


class Node(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, on_delete=models.CASCADE)
    objects = Manager.from_queryset(ExtendedQuerySet)()  # type: ignore[django-manager]


class TestUUIDModel(UUIDModel):
    text = models.CharField(max_length=255)
    parent = models.ForeignKey("TestUUIDModel", null=True, on_delete=models.CASCADE)


class SecretModel(models.Model):
    secret = SecretField()


class URLSecretModel(models.Model):
    # num_bytes=25 forces the base64 algorithm to pad
    secret = URLSecretField(num_bytes=25, min_bytes=25)
