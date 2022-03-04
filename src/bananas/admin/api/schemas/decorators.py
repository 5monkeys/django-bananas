from typing import Callable, Optional, Sequence, TypeVar

from django.http.response import HttpResponseBase

T = TypeVar("T", bound=Callable[..., HttpResponseBase])


def tags(
    include: Optional[Sequence[str]] = None, exclude: Optional[Sequence[str]] = None
) -> Callable[[T], T]:
    def decorator(view: T) -> T:
        view.include_tags = include  # type: ignore[attr-defined]
        view.exclude_tags = exclude  # type: ignore[attr-defined]
        return view

    return decorator
