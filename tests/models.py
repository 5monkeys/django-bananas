from django.db import models
from django.db.models.manager import Manager

from bananas.models import TimeStampedModel
from bananas.query import ExtendedQuerySet


class Parent(TimeStampedModel):
    objects = Manager.from_queryset(ExtendedQuerySet)()


class Child(TimeStampedModel):
    parent = models.ForeignKey(Parent)
