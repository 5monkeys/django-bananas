import django

__all__ = (
    'get_resolver', 'reverse', 'URLPattern',
    'URLResolver', 'urlpatterns'
)


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
