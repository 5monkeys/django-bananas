from django.db import models
from django.db.models.manager import Manager

from bananas.models import TimeStampedModel
from bananas.query import ExtendedQuerySet


class Parent(TimeStampedModel):
    name = models.CharField(max_length=255)
    objects = Manager.from_queryset(ExtendedQuerySet)()


class Child(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Parent, null=True)
    objects = Manager.from_queryset(ExtendedQuerySet)()
