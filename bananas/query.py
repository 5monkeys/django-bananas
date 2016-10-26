import logging
from itertools import chain
from django.db.models.query import QuerySet, ValuesQuerySet

MISSING = object()

_log = logging.getLogger(__name__)


class ModelDict(dict):

    _nested = None

    def __getattr__(self, item):
        """
        Try to to get attribute as key item.
        Fallback on prefixed nested keys.
        Finally fallback on real attribute lookup.
        """
        try:
            return self.__getitem__(item)
        except KeyError:
            try:
                return self.__getnested__(item)
            except KeyError:
                return self.__getattribute__(item)

    def __getnested__(self, item):
        """
        Find existing items prefixed with given item
        and return a new ModelDict containing matched keys,
        stripped from prefix.

        :param str item: Item prefix key to find
        :return ModelDict:
        """
        # Ensure _nested cache
        if self._nested is None:
            self._nested = {}

        # Try to get previously accessed/cached nested item
        value = self._nested.get(item, MISSING)

        if value is not MISSING:
            # Return previously accessed nested item
            return value

        else:
            # Find any keys matching nested prefix
            prefix = item + '__'
            keys = [key for key in self.keys() if key.startswith(prefix)]

            if keys:
                # Construct nested dict of matched keys, stripped from prefix
                n = ModelDict({key[len(item)+2:]: self[key] for key in keys})

                # Cache and return
                self._nested[item] = n
                return n

        # Item not a nested key, raise
        raise KeyError(item)

    @classmethod
    def from_model(cls, model, *fields, **named_fields):
        """
        Work-in-progress constructor,
        consuming fields and values from django model instance.
        """
        d = ModelDict()

        if not (fields or named_fields):
            # Default to all fields
            fields = [f.attname for f in model._meta.concrete_fields]

        not_found = object()

        for name, field in chain(zip(fields, fields), named_fields.items()):
            _fields = field.split('__')
            value = model
            for i, _field in enumerate(_fields, start=1):
                # NOTE: we don't want to rely on hasattr here
                previous_value = value
                value = getattr(previous_value, _field, not_found)

                if value is not_found:
                    if _field in dir(previous_value):
                        raise ValueError(
                            '{!r}.{} had an AttributeError exception'
                            .format(previous_value, _field))
                    else:
                        raise AttributeError(
                            '{!r} does not have {!r} attribute'
                            .format(previous_value, _field))

                elif value is None:
                    if name not in named_fields:
                        name = '__'.join(_fields[:i])
                    break

            d[name] = value

        return d


class ModelDictValuesQuerySet(ValuesQuerySet):

    def iterator(self):
        return (ModelDict(v) for v in super(ModelDictValuesQuerySet,
                                            self).iterator())


class ModelDictQuerySetMixin:

    def dicts(self, *fields):
        return self._clone(klass=ModelDictValuesQuerySet, setup=True,
                           _fields=fields)


class ModelDictQuerySet(ModelDictQuerySetMixin, QuerySet):
    pass


class ModelDictManagerMixin:

    def dicts(self, *fields):
        return self.get_queryset().dicts(*fields)

    def get_queryset(self):
        return ModelDictQuerySet(self.model, using=self._db)


class ExtendedValuesQuerySet(ValuesQuerySet):
    """
    Extended `ValuesQuerySet` with support for renaming fields
    and choice of object class.
    """
    _values_class = dict

    @property
    def named_fields(self):
        return getattr(self, '_named_fields')

    def rename_fields(self, names):
        named_fields = self.named_fields
        if named_fields:
            names = [named_fields.get(name, name) for name in names]
        return names

    def iterator(self):
        # Purge any extra columns that haven't been explicitly asked for
        extra_names = list(self.query.extra_select)
        field_names = self.field_names
        annotation_names = list(self.query.annotation_select)

        # Modified super(); rename fields given in queryset.values() kwargs
        names = self.rename_fields(extra_names + field_names + annotation_names)

        for row in self.query.get_compiler(self.db).results_iter():
            yield self._values_class(zip(names, row))

    def _clone(self, klass=None, setup=False, **kwargs):
        kwargs.update(_named_fields=self.named_fields,
                      _values_class=self._values_class,
                      klass=klass,
                      setup=setup)

        return super()._clone(**kwargs)


class ExtendedModelDictQuerySetMixin:

    def dicts(self, *fields, **named_fields):
        if named_fields:
            named_fields = {value: key for key, value in named_fields.items()}
            fields = fields + tuple(named_fields.keys())

        return self._clone(klass=ExtendedValuesQuerySet, setup=True,
                           _fields=fields, _named_fields=named_fields,
                           _values_class=ModelDict)


class ExtendedQuerySet(ExtendedModelDictQuerySetMixin, QuerySet):
    pass
