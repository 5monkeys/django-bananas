import django


def urlpatterns(*urls):
    if django.VERSION < (1, 10):
        try:
            from django.conf.urls.defaults import patterns
        except ImportError:
            from django.conf.urls import patterns

        return patterns('', *urls)

    # else
    return list(urls)
