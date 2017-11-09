import sys
from collections import OrderedDict

import django
from django.core.management import BaseCommand
from ... import compat


def collect_urls(urls=None, namespace=None, prefix=None):
    if urls is None:
        urls = compat.get_resolver(urlconf=None)
    prefix = prefix or []
    if isinstance(urls, compat.URLResolver):
        res = []
        if django.VERSION < (2, 0):
            pattern = urls.regex.pattern
        else:
            pattern = urls.pattern.regex.pattern
        for x in urls.url_patterns:
            res += collect_urls(x, namespace=urls.namespace or namespace,
                                prefix=prefix + [pattern])
        return res
    elif isinstance(urls, compat.URLPattern):
        if django.VERSION < (1, 10):
            callback = urls._callback
            lookup_str = callback.__module__ + '.'
            if hasattr(callback, '__name__'):
                lookup_str += callback.__name__
            else:
                lookup_str += callback.__class__.__name__
        else:  # pragma: no cover
            lookup_str = urls.lookup_str

        if django.VERSION < (2, 0):
            pattern = urls.regex.pattern
        else:
            pattern = urls.pattern.regex.pattern
        return [OrderedDict([('namespace', namespace),
                             ('name', urls.name),
                             ('pattern', prefix + [pattern]),
                             ('lookup_str', lookup_str),
                             ('default_args', dict(urls.default_args))])]
    else:  # pragma: no cover
        raise NotImplementedError(repr(urls))


def show_urls():
    all_urls = collect_urls()

    max_lengths = {}
    for u in all_urls:
        for k in ['pattern', 'default_args']:
            u[k] = str(u[k])
        for k, v in list(u.items())[:-1]:
            u[k] = v = v or ''
            # Skip app_list due to length (contains all app names)
            if (u['namespace'], u['name'], k) == \
                    ('admin', 'app_list', 'pattern'):
                continue
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))

    for u in sorted(all_urls, key=lambda x: (x['namespace'], x['name'])):
        sys.stdout.write(' | '.join(
            ('{:%d}' % max_lengths.get(k, len(v))).format(v)
            for k, v in u.items()) + '\n')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        show_urls()
