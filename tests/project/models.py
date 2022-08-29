from typing import TYPE_CHECKING, NoReturn

from django.db import models
from django.db.models import Model
from django.db.models.manager import BaseManager, Manager

from bananas.models import SecretField, TimeStampedModel, URLSecretField, UUIDModel
from bananas.query import ExtendedQuerySet, ModelDictManagerMixin


class SimpleManager(ModelDictManagerMixin, Manager):
    pass


class Simple(Model):
    name = models.CharField(max_length=255)
    objects = SimpleManager()


if TYPE_CHECKING:

    class ParentQuerySet(ExtendedQuerySet["Parent"]):
        ...

else:

    class ParentQuerySet(ExtendedQuerySet):
        ...


ParentManager = BaseManager.from_queryset(ParentQuerySet)


class Parent(TimeStampedModel):
    name = models.CharField(max_length=255)
    objects = ParentManager()

    @property
    def attribute_error(self) -> NoReturn:
        raise AttributeError()

    @property
    def version(self) -> str:
        return str(self.pk) + ":" + str(self.date_modified)


if TYPE_CHECKING:

    class ChildQuerySet(ExtendedQuerySet["Child"]):
        ...

else:

    class ChildQuerySet(ExtendedQuerySet):
        ...


ChildManager = BaseManager.from_queryset(ChildQuerySet)


class Child(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Parent, null=True, on_delete=models.CASCADE)
    objects = ChildManager()


if TYPE_CHECKING:

    class NodeQuerySet(ExtendedQuerySet["Node"]):
        ...

else:

    class NodeQuerySet(ExtendedQuerySet):
        ...


NodeManager = BaseManager.from_queryset(NodeQuerySet)


class Node(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, on_delete=models.CASCADE)
    objects = NodeManager()


class TestUUIDModel(UUIDModel):
    text = models.CharField(max_length=255)
    parent = models.ForeignKey("TestUUIDModel", null=True, on_delete=models.CASCADE)


class SecretModel(models.Model):
    secret = SecretField()


class URLSecretModel(models.Model):
    # num_bytes=25 forces the base64 algorithm to pad
    secret = URLSecretField(num_bytes=25, min_bytes=25)
