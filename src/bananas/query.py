import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
)

from django.db.models import Model
from django.db.models.expressions import Combinable
from django.db.models.query import QuerySet
from typing_extensions import Protocol

from .models import ModelDict

if TYPE_CHECKING:
    from django.db.models.query import _QuerySet

_log = logging.getLogger(__name__)

T = TypeVar("T", bound="QuerySet[Model]")


class ModelDictIterable:
    def __init__(self, queryset: T) -> None:
        self.queryset = queryset
        self.named_fields: Mapping[str, str] = self.queryset._hints.get("_named_fields")  # type: ignore[attr-defined]

    def __iter__(self) -> Iterator[ModelDict]:
        queryset = self.queryset
        query = queryset.query
        compiler = query.get_compiler(queryset.db)

        if hasattr(query, "selected") and query.selected:
            names = list(query.selected)
        else:
            extra_names: List[str] = list(query.extra_select)
            field_names: List[str] = list(query.values_select)
            annotation_names: List[str] = list(query.annotation_select)

            # Modified super(); rename fields given in queryset.values() kwargs
            names = extra_names + field_names + annotation_names

        if self.named_fields:
            names = self.rename_fields(names)

        for row in compiler.results_iter():
            yield ModelDict(zip(names, row))

    def rename_fields(self, names: Iterable[str]) -> List[str]:
        named_fields = {value: key for key, value in self.named_fields.items()}
        names = [named_fields.get(name, name) for name in names]
        return names


_MT_co = TypeVar("_MT_co", bound=Model, covariant=True)


class IsQuerySet(Protocol[_MT_co]):
    def values(
        self, *fields: Union[str, Combinable], **expressions: Any
    ) -> "_QuerySet[_MT_co, ModelDict]": ...


class ModelDictQuerySetMixin:
    def dicts(
        self: IsQuerySet[_MT_co], *fields: str, **named_fields: str
    ) -> "_QuerySet[_MT_co, ModelDict]":
        if named_fields:
            fields += tuple(named_fields.values())

        clone = self.values(*fields)
        clone._iterable_class = ModelDictIterable

        # QuerySet._hints is a dict object used by db router
        # to aid deciding which db should get a request. Currently
        # django only supports `instance`, so it's probably
        # fine to set a custom key on this dict as it's a guaranteed
        # way that it'll be returned with the QuerySet instance
        # while leaving the queryset intact
        clone._add_hints(**{"_named_fields": named_fields})

        return clone


_MT = TypeVar("_MT", bound=Model)


if TYPE_CHECKING:

    class ModelDictQuerySet(
        ModelDictQuerySetMixin,
        QuerySet[_MT],
        IsQuerySet[_MT],
        Generic[_MT],
    ):
        pass

else:

    class ModelDictQuerySet(ModelDictQuerySetMixin, QuerySet):
        pass


class IsManager(Protocol[_MT]):
    model: Type[_MT]
    _db: Optional[str]


class ModelDictManagerMixin:
    def dicts(
        self, *fields: str, **named_fields: str
    ) -> "_QuerySet[_MT_co, ModelDict]":
        # Mypy: `self` types don't add up
        queryset = self.get_queryset()  # type: ignore[misc]
        return queryset.dicts(*fields, **named_fields)

    def get_queryset(self: IsManager[_MT]) -> ModelDictQuerySet:
        return ModelDictQuerySet(self.model, using=self._db)


ExtendedQuerySet = ModelDictQuerySet  # Left for compatibility
