from ..utils import ModelDict


def _create_names_and_iterable(queryset):
    query = queryset.query
    compiler = query.get_compiler(queryset.db)

    field_names = list(query.values_select)
    extra_names = list(query.extra_select)
    annotation_names = list(query.annotation_select)

    # extra(select=...) cols are always at the start of the row.
    names = extra_names + field_names + annotation_names
    rows = compiler.results_iter()
    return names, rows


class ModelDictQuerySetMixin:

    def dicts(self, *fields):
        def _iterable_func(queryset):
            names, rows = _create_names_and_iterable(queryset)
            for row in rows:
                yield ModelDict(zip(names, row))

        clone = self._values(*fields)
        clone._iterable_class = _iterable_func
        return clone


class ExtendedModelDictQuerySetMixin:

    def dicts(self, *fields, **named_fields):
        if named_fields:
            named_fields = {value: key for key, value in named_fields.items()}
            fields = fields + tuple(named_fields.keys())

        def _iterable_func(queryset):
            names, rows = _create_names_and_iterable(queryset)

            if named_fields:
                names = [named_fields.get(name, name) for name in names]

            for row in rows:
                yield ModelDict(zip(names, row))

        clone = self._values(*fields)
        clone._iterable_class = _iterable_func
        return clone
