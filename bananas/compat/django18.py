from django.db.models.query import ValuesQuerySet

from bananas.models import ModelDict


class ExtendedValuesQuerySet(ValuesQuerySet):
    """
    Extended `ValuesQuerySet` with support for renaming fields
    and choice of object class.
    """

    _values_class = dict

    @property
    def named_fields(self):
        return getattr(self, "_named_fields")

    def rename_fields(self, names):
        named_fields = {value: key for key, value in self.named_fields.items()}
        names = [named_fields.get(name, name) for name in names]
        return names

    def iterator(self):
        # Purge any extra columns that haven't been explicitly asked for
        extra_names = list(self.query.extra_select)
        field_names = self.field_names
        annotation_names = list(self.query.annotation_select)

        # Modified super(); rename fields given in queryset.values() kwargs
        names = self.rename_fields(extra_names + field_names + annotation_names)
        if self.named_fields:
            names = self.rename_fields(names)

        for row in self.query.get_compiler(self.db).results_iter():
            yield self._values_class(zip(names, row))

    def _clone(self, klass=None, setup=False, **kwargs):
        kwargs.update(
            _named_fields=self.named_fields,
            _values_class=self._values_class,
            klass=klass,
            setup=setup,
        )

        return super()._clone(**kwargs)


class ModelDictQuerySetMixin:
    def dicts(self, *fields, **named_fields):
        if named_fields:
            fields += tuple(named_fields.values())

        return self._clone(
            klass=ExtendedValuesQuerySet,
            setup=True,
            _fields=fields,
            _named_fields=named_fields,
            _values_class=ModelDict,
        )
