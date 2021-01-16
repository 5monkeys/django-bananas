import abc
import datetime
import operator
from functools import wraps
from typing import Callable, FrozenSet, Generic, Optional, TypeVar

from rest_framework import mixins
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer, ModelSerializer
from rest_framework.viewsets import GenericViewSet
from typing_extensions import Final, final

from bananas.models import TimeStampedModel

from . import errors
from .utils import HeaderError, parse_header_datetime, parse_header_etags

__all__ = (
    "Fence",
    "FencedUpdateModelMixin",
    "header_date_parser",
    "parse_date_modified",
    "allow_if_unmodified_since",
    "header_etag_parser",
    "allow_if_match",
)

TokenType = TypeVar("TokenType")
InstanceType = TypeVar("InstanceType")


@final
class Fence(abc.ABC, Generic[InstanceType, TokenType]):
    def __init__(
        self,
        get_token: Callable[[Request], TokenType],
        compare: Callable[[TokenType, TokenType], bool],
        get_version: Callable[[InstanceType], Optional[TokenType]],
    ) -> None:
        self._get_token: Final = get_token
        self._compare: Final = compare
        self._get_version: Final = get_version

    def check(self, request: Request, instance: InstanceType) -> bool:
        version = self._get_version(instance)
        if version is None:
            # We might want to expose control of this behavior. For if-unmodified-since
            # it makes sense to return true here, but it might not for
            # if-modified-since other conditionals.
            return True
        return self._compare(version, self._get_token(request))


class FencedUpdateModelMixin(abc.ABC):
    @property
    @abc.abstractmethod
    def fence(self) -> Fence:
        ...

    def perform_update(self, serializer: BaseSerializer) -> None:
        # mypy's advanced self types don't work with super calls so we use an assertion
        # here instead.
        assert isinstance(self, GenericViewSet)
        assert isinstance(self, mixins.UpdateModelMixin)
        assert isinstance(serializer, ModelSerializer)
        if not self.fence.check(self.request, serializer.instance):
            raise errors.PreconditionFailed(
                "The resource does not fulfill the given preconditions"
            )
        super().perform_update(serializer)  # type: ignore[misc]


def header_date_parser(header: str) -> Callable[[Request], datetime.datetime]:
    def parse(request: Request) -> datetime.datetime:
        try:
            return parse_header_datetime(request, header)
        except HeaderError as e:
            raise e.as_api_error()

    return parse


def parse_date_modified(instance: TimeStampedModel) -> Optional[datetime.datetime]:
    return (
        instance.date_modified.replace(microsecond=0)
        if instance.date_modified
        else None
    )


allow_if_unmodified_since: Final = Fence[TimeStampedModel, datetime.datetime](
    get_token=header_date_parser("If-Unmodified-Since"),
    compare=operator.le,
    get_version=parse_date_modified,
)


def header_etag_parser(header: str) -> Callable[[Request], FrozenSet[str]]:
    def parse(request: Request) -> FrozenSet[str]:
        try:
            return parse_header_etags(request, header)
        except HeaderError as e:
            raise e.as_api_error()

    return parse


T = TypeVar("T")


def as_set(
    fn: Callable[[InstanceType], Optional[T]]
) -> Callable[[InstanceType], Optional[FrozenSet[T]]]:
    @wraps(fn)
    def wrapper(instance: InstanceType) -> Optional[FrozenSet[T]]:
        version = fn(instance)
        return None if version is None else frozenset({version})

    return wrapper


def allow_if_match(
    version_getter: Callable[[InstanceType], Optional[str]]
) -> Fence[InstanceType, FrozenSet[str]]:
    return Fence(
        get_token=header_etag_parser("If-Match"),
        compare=operator.le,
        get_version=as_set(version_getter),
    )
