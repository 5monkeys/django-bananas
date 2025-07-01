from typing import TYPE_CHECKING, NoReturn

from django.db import models
from django.db.models import Model
from django.db.models.manager import Manager

from bananas.models import (
    SecretField,
    TimeStampedModel,
    URLSecretField,
    UUIDModel as BananasUUIDModel,
)
from bananas.query import ExtendedQuerySet, ModelDictManagerMixin


class BananasModel(Model):
    """
    Base for test models that sets app_label, so they play nicely
    """

    class Meta:
        app_label = "tests"
        abstract = True


class SimpleManager(ModelDictManagerMixin, Manager):
    pass


class Simple(BananasModel):
    name = models.CharField(max_length=255)
    objects = SimpleManager()


if TYPE_CHECKING:

    class ParentQuerySet(ExtendedQuerySet["Parent"]): ...

else:

    class ParentQuerySet(ExtendedQuerySet): ...


ParentManager = Manager.from_queryset(ParentQuerySet)


class Parent(TimeStampedModel, BananasModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    objects = ParentManager()

    @property
    def attribute_error(self) -> NoReturn:
        raise AttributeError()

    @property
    def version(self) -> str:
        return str(self.pk) + ":" + str(self.date_modified)


if TYPE_CHECKING:

    class ChildQuerySet(ExtendedQuerySet["Child"]): ...

else:

    class ChildQuerySet(ExtendedQuerySet): ...


ChildManager = Manager.from_queryset(ChildQuerySet)


class Child(TimeStampedModel, BananasModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    parent = models.ForeignKey(Parent, null=True, on_delete=models.CASCADE)
    objects = ChildManager()


if TYPE_CHECKING:

    class NodeQuerySet(ExtendedQuerySet["Node"]): ...

else:

    class NodeQuerySet(ExtendedQuerySet): ...


NodeManager = Manager.from_queryset(NodeQuerySet)


class Node(TimeStampedModel, BananasModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, on_delete=models.CASCADE)
    objects = NodeManager()


class UUIDModel(BananasUUIDModel, BananasModel):
    text = models.CharField(max_length=255)
    parent = models.ForeignKey("UUIDModel", null=True, on_delete=models.CASCADE)


class SecretModel(BananasModel):
    secret = SecretField()


class URLSecretModel(BananasModel):
    # num_bytes=25 forces the base64 algorithm to pad
    secret = URLSecretField(num_bytes=25, min_bytes=25)
