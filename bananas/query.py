from django.db.models.query import QuerySet, ValuesQuerySet


class ModelValues(dict):

    # TODO: Add lazy nested dot functionality, i.e. obj.x__y -> obj.x.y

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            return getattr(self, item)


class NamedValuesQuerySet(ValuesQuerySet):

    def iterator(self):
        """
        Source copied from super to decrease nof dict initializations
        """
        # Purge any extra columns that haven't been explicitly asked for
        extra_names = list(self.query.extra_select)
        field_names = self.field_names
        annotation_names = list(self.query.annotation_select)

        names = extra_names + field_names + annotation_names

        # Modified super(); rename fields given in queryset.values() kwargs
        if hasattr(self, '_renames'):
            names = [self._renames.get(name, name) for name in names]

        for row in self.query.get_compiler(self.db).results_iter():
            yield ModelValues(zip(names, row))

    def _clone(self, klass=None, setup=False, **kwargs):
        kwargs.update(_renames=getattr(self, '_renames', {}))
        return super()._clone(klass=klass, setup=setup, **kwargs)


class ExtendedValuesMixin:

    def values(self, *fields, **named_fields):
        _fields = fields + tuple(named_fields.values())
        _renames = {value: key for key, value in named_fields.items()}
        return self._clone(klass=NamedValuesQuerySet, setup=True,
                           _fields=_fields, _renames=_renames)


class ExtendedValuesQuerySet(ExtendedValuesMixin, QuerySet):
    pass
