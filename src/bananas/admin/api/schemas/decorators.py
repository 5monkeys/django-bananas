from typing import Callable, Optional, Sequence

from django.http.response import HttpResponseBase

View = Callable[..., HttpResponseBase]


def tags(
    include: Optional[Sequence[str]] = None, exclude: Optional[Sequence[str]] = None
) -> Callable[[View], View]:
    def decorator(view: View) -> View:
        view.include_tags = include  # type: ignore[attr-defined]
        view.exclude_tags = exclude  # type: ignore[attr-defined]
        return view

    return decorator
