import logging

from functools import partial
from os import environ

from django.conf import global_settings


__all__ = [
    'parse_bool', 'parse_int', 'parse_tuple', 'parse_list', 'parse_set'
]

log = logging.getLogger(__name__)

UNDEFINED = object()

UNSUPPORTED_ENV_SETTINGS = (
    'ADMINS',
    'MANAGERS',
    'LANGUAGES',
    'DISALLOWED_USER_AGENTS',
    'IGNORABLE_404_URLS',
    'TEMPLATES',
)

SETTINGS_TYPES = {
    'LANGUAGE_COOKIE_AGE': int,
    'EMAIL_TIMEOUT': int,
    'FILE_UPLOAD_PERMISSIONS': int,
    'FILE_UPLOAD_DIRECTORY_PERMISSIONS': int,
}


def parse_str(value):
    """
    Clean string.

    :param str value: Original str.
    :return: str: Cleaned str.
    """
    return value.strip()


def parse_bool(value):
    """
    Parse string to bool.

    :param str value: String value to parse as bool
    :return bool:
    """
    boolean = parse_str(value).capitalize()

    if boolean in ('True', 'Yes', 'On', '1'):
        return True
    elif boolean in ('False', 'No', 'Off', '0'):
        return False
    else:
        raise ValueError('Unable to parse boolean value "{}"'.format(value))


def parse_int(value):
    """
    Parse numeric string to int. Supports oct formatted string.

    :param str value: String value to parse as int
    :return int:
    """
    value = parse_str(value=value)
    if value.startswith('0'):
        return int(value.lstrip('0o'), 8)
    else:
        return int(value)


def parse_iterable(typ, value):
    """
    Parse comma separated string into typed iterable.

    :param typ: Type to cast iterable to
    :param value: String value to parse as iterable
    :return: Given type
    """
    return typ(parse_str(v) for v in value.split(','))


parse_tuple = partial(parse_iterable, tuple)
parse_list = partial(parse_iterable, list)
parse_set = partial(parse_iterable, set)


def get_parser(typ):
    """
    Return appropriate parser for given type.

    :param typ: Type to get parser for.
    :return function: Parser
    """
    try:
        return {
            str: parse_str,
            bool: parse_bool,
            int: parse_int,
            tuple: parse_tuple,
            list: parse_list,
            set: parse_set,
        }[typ]
    except KeyError:
        raise NotImplementedError("Unsupported setting type: %r", typ)


def get_settings():
    """
    Get and parse prefixed django settings from env.

    TODO: Implement support for complex settings
        DATABASES = {}
        CACHES = {}
        INSTALLED_APPS -> EXCLUDE_APPS ?

    :return dict:
    """
    settings = {}
    prefix = environ.get('DJANGO_SETTINGS_PREFIX', 'DJANGO_')

    for key, value in environ.items():
        _, _, key = key.partition(prefix)
        if key:
            if key in UNSUPPORTED_ENV_SETTINGS:
                raise ValueError('Django setting "{}" can not be '
                                 'configured through environment.'.format(key))

            default_value = getattr(global_settings, key, UNDEFINED)

            if default_value is not UNDEFINED:
                if default_value is None and key in SETTINGS_TYPES.keys():
                    # Handle typed django settings defaulting to None
                    parse = get_parser(SETTINGS_TYPES[key])
                else:
                    # Determine parser by django setting type
                    parse = get_parser(type(default_value))

                value = parse(value)

            settings[key] = value

    return settings


class EnvironWrapper(object):
    """
    Wrapper around os environ with type conversion support.
    """
    __delitem__ = environ.__delitem__
    __getitem__ = environ.__getitem__
    __setitem__ = environ.__setitem__
    __contains__ = environ.__contains__

    def __getattr__(self, item):
        return getattr(environ, item)

    def parse(self, parser, key, default=None):
        value = environ.get(key, UNDEFINED)
        if value is UNDEFINED:
            return default
        try:
            return parser(value)
        except ValueError:
            log.warning((
                'Unable to parse environment variable '
                '{key}={value}'
            ).format(
                key=key,
                value=value,
            ))
            return default

    def get_bool(self, key, default=None):
        return self.parse(parse_bool, key, default=default)

    def get_int(self, key, default=None):
        return self.parse(parse_int, key, default=default)

    def get_tuple(self, key, default=None):
        return self.parse(parse_tuple, key, default=default)

    def get_list(self, key, default=None):
        return self.parse(parse_list, key, default=default)

    def get_set(self, key, default=None):
        return self.parse(parse_set, key, default=default)


env = EnvironWrapper()
