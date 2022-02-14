from typing import Any, Mapping, Optional, cast

from rest_framework.request import Request


class FakeRequest:
    def __init__(self, headers: Optional[Mapping[str, str]] = None) -> None:
        self.headers = headers or {}

    @classmethod
    def fake(cls, *args: Any, **kwargs: Any) -> Request:
        return cast(Request, cls(*args, **kwargs))
