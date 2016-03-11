import logging

from django.db.models.query import QuerySet

from .compat import ExtendedModelDictQuerySetMixin, ModelDictQuerySetMixin
from .utils import ModelDict

__all__ = [
    'ModelDict', 'ModelDictQuerySet', 'ModelDictManagerMixin', 'ExtendedQuerySet'
]


_log = logging.getLogger(__name__)


class ModelDictQuerySet(ModelDictQuerySetMixin, QuerySet):
    pass


class ModelDictManagerMixin:

    def dicts(self, *fields):
        return self.get_queryset().dicts(*fields)

    def get_queryset(self):
        return ModelDictQuerySet(self.model, using=self._db)


class ExtendedQuerySet(ExtendedModelDictQuerySetMixin, QuerySet):
    pass
