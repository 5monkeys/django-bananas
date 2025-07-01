import abc
import datetime
import operator
from functools import wraps
from typing import (
    Any,
    Callable,
    Final,
    FrozenSet,
    Generic,
    List,
    NoReturn,
    Optional,
    TypeVar,
    cast,
)

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, QuerySet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.mixins import UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ModelSerializer
from rest_framework.viewsets import GenericViewSet
from typing_extensions import Protocol, final

from bananas.admin.api.schemas.yasg import BananasSwaggerSchema
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
        openapi_parameter: openapi.Parameter,
        rejection: Optional[Exception] = None,
    ) -> None:
        self._get_token: Final = get_token
        self._compare: Final = compare
        self._get_version: Final = get_version
        self._rejection: Final = (
            rejection
            if rejection is not None
            else errors.PreconditionFailed(
                "The resource does not fulfill the given preconditions"
            )
        )
        self.openapi_parameter: Final = openapi_parameter

    def check(self, request: Request, instance: InstanceType) -> bool:
        version = self._get_version(instance)
        if version is None:
            # We might want to expose control of this behavior. For if-unmodified-since
            # it makes sense to return true here, but it might not for
            # if-modified-since other conditionals.
            return True
        return self._compare(version, self._get_token(request))

    def reject(self) -> NoReturn:
        raise self._rejection

    def validate(self, request: Request, instance: InstanceType) -> None:
        if not self.check(request, instance):
            self.reject()


class FenceAwareSwaggerAutoSchema(BananasSwaggerSchema):
    update_methods = ("PUT", "PATCH")

    def add_manual_parameters(
        self, parameters: List[openapi.Parameter]
    ) -> List[openapi.Parameter]:
        parameters = super().add_manual_parameters(parameters)
        if (
            isinstance(self.view, FencedUpdateModelMixin)
            and self.method in self.update_methods
        ):
            return [*parameters, self.view.fence.openapi_parameter]
        return parameters


_MT_co = TypeVar("_MT_co", bound=Model, covariant=True)


class UsesQuerySet(Protocol[_MT_co]):
    def get_queryset(self) -> "QuerySet[_MT_co]": ...


class FencedUpdateModelMixin(UpdateModelMixin, abc.ABC):
    @property
    @abc.abstractmethod
    def fence(self) -> Fence: ...

    # django-restframework uses an "advanced self-type" on self in
    # perform_update() which subtly breaks subclassing. We try to remedy this by
    # implementing get_queryset() so that we fulfill the self-type in the
    # overridden method.
    # See https://github.com/typeddjango/djangorestframework-stubs/issues/132
    def get_queryset(self: UsesQuerySet[_MT_co]) -> "QuerySet[_MT_co]":
        return cast(UsesQuerySet[_MT_co], super()).get_queryset()

    def perform_update(self, serializer: BaseSerializer) -> None:
        # mypy's advanced self types don't work with super calls so we use an assertion
        # here instead.
        assert isinstance(self, GenericViewSet)
        assert isinstance(serializer, ModelSerializer)
        self.fence.validate(self.request, serializer.instance)
        super().perform_update(serializer)

    @swagger_auto_schema(auto_schema=FenceAwareSwaggerAutoSchema)
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(auto_schema=FenceAwareSwaggerAutoSchema)
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().partial_update(request, *args, **kwargs)


def header_date_parser(header: str) -> Callable[[Request], datetime.datetime]:
    def parse(request: Request) -> datetime.datetime:
        try:
            return parse_header_datetime(request, header)
        except HeaderError as e:
            raise e.as_api_error() from e

    return parse


def parse_date_modified(instance: TimeStampedModel) -> Optional[datetime.datetime]:
    return (
        instance.date_modified.replace(microsecond=0)
        if instance.date_modified
        else None
    )


def allow_if_unmodified_since() -> Fence[TimeStampedModel, datetime.datetime]:
    if not settings.USE_TZ:
        raise ImproperlyConfigured(
            "{} does not support settings.USE_TZ=False.".format(
                allow_if_unmodified_since.__name__
            )
        )
    return Fence(
        get_token=header_date_parser("If-Unmodified-Since"),
        compare=operator.le,
        get_version=parse_date_modified,
        openapi_parameter=openapi.Parameter(
            in_=openapi.IN_HEADER,
            name="If-Unmodified-Since",
            type=openapi.TYPE_STRING,
            required=True,
            description=(
                "Time of last edit of the client's representation of the resource in "
                "RFC7231 format."
            ),
        ),
    )


def header_etag_parser(header: str) -> Callable[[Request], FrozenSet[str]]:
    def parse(request: Request) -> FrozenSet[str]:
        try:
            return parse_header_etags(request, header)
        except HeaderError as e:
            raise e.as_api_error() from e

    return parse


T = TypeVar("T")


def as_set(
    fn: Callable[[InstanceType], Optional[T]],
) -> Callable[[InstanceType], Optional[FrozenSet[T]]]:
    @wraps(fn)
    def wrapper(instance: InstanceType) -> Optional[FrozenSet[T]]:
        version = fn(instance)
        return None if version is None else frozenset({version})

    return wrapper


def allow_if_match(
    version_getter: Callable[[InstanceType], Optional[str]],
) -> Fence[InstanceType, FrozenSet[str]]:
    return Fence(
        get_token=header_etag_parser("If-Match"),
        compare=operator.le,
        get_version=as_set(version_getter),
        openapi_parameter=openapi.Parameter(
            in_=openapi.IN_HEADER,
            name="If-Match",
            type=openapi.TYPE_STRING,
            required=True,
            description=(
                "Version or list of versions of the clients representation of the "
                "resource."
            ),
        ),
    )
