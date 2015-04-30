from itertools import chain
from django.db.models.query import QuerySet, ValuesQuerySet

MISSING = object()


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

        for name, field in chain(zip(fields, fields), named_fields.items()):
            _fields = field.split('__')
            value = model
            for i, _field in enumerate(_fields, start=1):
                value = getattr(value, _field)
                if value is None:
                    name = '__'.join(_fields[:i])
                    break

            d[name] = value

        return d


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
        """
        Source copied from super to decrease nof dict initializations
        """
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
                      _values_class=self._values_class)
        return super()._clone(klass=klass, setup=setup, **kwargs)


class DictValuesMixin:

    def dicts(self, *fields, **named_fields):
        if named_fields:
            named_fields = {value: key for key, value in named_fields.items()}
            fields = fields + tuple(named_fields.keys())
        return self._clone(klass=ExtendedValuesQuerySet, setup=True,
                           _fields=fields, _named_fields=named_fields,
                           _values_class=ModelDict)


class ExtendedQuerySet(DictValuesMixin, QuerySet):
    pass
