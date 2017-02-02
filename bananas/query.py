import logging

import django
from django.db.models.query import QuerySet

from .models import ModelDict


_log = logging.getLogger(__name__)


class ModelDictIterable(object):

    def __init__(self, queryset, named_fields=None):
        self.queryset = queryset
        self.named_fields = named_fields

    def __iter__(self):
        queryset = self.queryset
        query = queryset.query
        compiler = query.get_compiler(queryset.db)

        field_names = list(query.values_select)
        extra_names = list(query.extra_select)
        annotation_names = list(query.annotation_select)

        # Modified super(); rename fields given in queryset.values() kwargs
        names = extra_names + field_names + annotation_names
        if self.named_fields:
            names = self.rename_fields(names)

        for row in compiler.results_iter():
            yield ModelDict(zip(names, row))

    def rename_fields(self, names):
        named_fields = {value: key for key, value in self.named_fields.items()}
        names = (named_fields.get(name, name) for name in names)
        return names


class ModelDictQuerySetMixin:
    """
    Supported by Django >= 1.9
    """
    def dicts(self, *fields, **named_fields):
        if named_fields:
            fields += tuple(named_fields.values())

        def iterable(queryset):
            return ModelDictIterable(queryset, named_fields)

        clone = self.values(*fields)
        clone._iterable_class = iterable
        return clone


if django.VERSION[:2] < (1, 9):
    """
    Patch ModelDictQuerySetMixin for old Django compatibility
    """
    from .compat.django18 import ModelDictQuerySetMixin


class ModelDictQuerySet(ModelDictQuerySetMixin, QuerySet):
    pass


class ModelDictManagerMixin:

    def dicts(self, *fields, **named_fields):
        return self.get_queryset().dicts(*fields, **named_fields)

    def get_queryset(self):
        return ModelDictQuerySet(self.model, using=self._db)


ExtendedQuerySet = ModelDictQuerySet  # Left for compatibility
