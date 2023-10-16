import sys
from collections import OrderedDict
from typing import Callable, Dict, List, Optional, Tuple, Union

from django.core.management import BaseCommand
from django.urls import URLPattern, URLResolver, get_resolver


def collect_urls(
    urls: Union[URLResolver, URLPattern, Tuple[str, Callable], None] = None,
    namespace: Optional[str] = None,
    prefix: Optional[list] = None,
) -> List["OrderedDict"]:
    if urls is None:
        urls = get_resolver(urlconf=None)
    prefix = prefix or []
    if isinstance(urls, URLResolver):
        res = []
        pattern = urls.pattern.regex.pattern
        for x in urls.url_patterns:
            res += collect_urls(
                x, namespace=urls.namespace or namespace, prefix=[*prefix, pattern]
            )
        return res
    elif isinstance(urls, URLPattern):
        lookup_str = urls.lookup_str
        pattern = urls.pattern.regex.pattern
        return [
            OrderedDict(
                [
                    ("namespace", namespace),
                    ("name", urls.name),
                    ("pattern", [*prefix, pattern]),
                    ("lookup_str", lookup_str),
                    ("default_args", dict(urls.default_args or {})),
                ]
            )
        ]
    else:  # pragma: no cover
        raise NotImplementedError(repr(urls))


def show_urls() -> None:
    all_urls = collect_urls()

    max_lengths: Dict[str, int] = {}
    for u in all_urls:
        for k in ["pattern", "default_args"]:
            u[k] = str(u[k])
        for k, v in list(u.items())[:-1]:
            u[k] = v = v or ""
            # Skip app_list due to length (contains all app names)
            if (u["namespace"], u["name"], k) == ("admin", "app_list", "pattern"):
                continue
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))

    for u in sorted(all_urls, key=lambda x: (x["namespace"], x["name"])):
        sys.stdout.write(
            " | ".join(
                ("{:%d}" % max_lengths.get(k, len(v))).format(v) for k, v in u.items()
            )
            + "\n"
        )


class Command(BaseCommand):
    def handle(self, *args: object, **kwargs: object) -> None:
        show_urls()
