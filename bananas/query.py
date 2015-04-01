from django.db.models.query import QuerySet, ValuesQuerySet


class ModelDict(dict):

    # TODO: Add lazy nested dot functionality, i.e. obj.x__y -> obj.x.y

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            return getattr(self, item)


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
