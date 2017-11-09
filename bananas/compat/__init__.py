import sys
import django

__all__ = (
    'urlsplit', 'parse_qs', 'get_resolver', 'reverse', 'URLPattern',
    'URLResolver', 'urlpatterns'
)

if sys.version_info < (3,):
    from urlparse import urlsplit, parse_qs
else:
    from urllib.parse import urlsplit, parse_qs


if django.VERSION < (2, 0):
    from django.core.urlresolvers import get_resolver, reverse
    from django.conf.urls import RegexURLPattern as URLPattern, \
        RegexURLResolver as URLResolver
else:
    from django.urls import get_resolver, reverse, URLPattern, URLResolver


def urlpatterns(*urls):
    if django.VERSION < (1, 10):
        from django.conf.urls import patterns
        return patterns('', *urls)

    return list(urls)
