import datetime
from typing import FrozenSet, Iterable

from django.utils.http import parse_http_date
from rest_framework.request import Request

from .errors import BadRequest

__all__ = (
    "HeaderError",
    "MissingHeader",
    "InvalidHeader",
    "parse_header_datetime",
    "parse_header_etags",
)


class HeaderError(ValueError):
    code = "invalid_header"

    def as_api_error(self) -> BadRequest:
        return BadRequest(detail=str(self), code=self.code)


class MissingHeader(HeaderError):
    code = "missing_header"

    def __init__(self, header: str) -> None:
        self.header = header
        super().__init__(f"Header missing in request: {header}")


class InvalidHeader(HeaderError):
    def __init__(self, header: str) -> None:
        self.header = header
        super().__init__(f"Malformed header in request: {header}")


def parse_header_datetime(request: Request, header: str) -> datetime.datetime:
    try:
        value = request.headers[header]
    except KeyError as exc:
        raise MissingHeader(header) from exc
    try:
        return datetime.datetime.fromtimestamp(
            parse_http_date(value), tz=datetime.timezone.utc
        )
    except ValueError as e:
        raise InvalidHeader(header) from e


# This can be inlined with a walrus expression but we need to keep support for pre 3.8.
def clean_tags(tags: Iterable[str]) -> Iterable[str]:
    for tag in tags:
        cleaned = tag.strip().strip('"')
        if cleaned:
            yield cleaned


def parse_header_etags(request: Request, header: str) -> FrozenSet[str]:
    try:
        parts = request.headers[header].split(",")
    except KeyError as exc:
        raise MissingHeader(header) from exc
    tags = frozenset(clean_tags(parts))
    if not tags:
        raise InvalidHeader(header)
    return tags
