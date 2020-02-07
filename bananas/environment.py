import logging
from os import environ
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from django.conf import global_settings
from typing_extensions import Final, Protocol

__all__ = (
    "safe_env",
    "env",
    "parse_bool",
    "parse_int",
    "parse_tuple",
    "parse_list",
    "parse_set",
    "parse_frozenset",
)

log = logging.getLogger(__name__)


class Undefined:
    ...


UNDEFINED: Final = Undefined()

UNSUPPORTED_ENV_SETTINGS: Final = (
    "ADMINS",
    "MANAGERS",
    "LANGUAGES",
    "DISALLOWED_USER_AGENTS",
    "IGNORABLE_404_URLS",
    "TEMPLATES",
)

SETTINGS_TYPES: Final[Mapping] = {
    "LANGUAGE_COOKIE_AGE": int,
    "EMAIL_TIMEOUT": int,
    "FILE_UPLOAD_PERMISSIONS": int,
    "FILE_UPLOAD_DIRECTORY_PERMISSIONS": int,
}


def parse_str(value: str) -> str:
    """
    Clean string.

    :param str value: Original str.
    :return: str: Cleaned str.
    """
    return value.strip()


def parse_bool(value: str) -> bool:
    """
    Parse string to bool.

    :param str value: String value to parse as bool
    :return bool:
    """
    boolean = parse_str(value).capitalize()

    if boolean in ("True", "Yes", "On", "1"):
        return True
    elif boolean in ("False", "No", "Off", "0"):
        return False
    raise ValueError('Unable to parse boolean value "{}"'.format(value))


def parse_int(value: str) -> int:
    """
    Parse numeric string to int. Supports oct formatted string.

    :param str value: String value to parse as int
    :return int:
    """
    value = parse_str(value=value)
    if value.startswith("0"):
        return int(value.lstrip("0o"), 8)
    return int(value)


class InstantiableCollection(Collection, Protocol):
    def __init__(self, iterable: Iterable) -> None:
        ...


IT = TypeVar("IT", bound=InstantiableCollection)


def parse_iterable(typ: Type[IT], value: str) -> IT:
    """
    Parse comma separated string into typed iterable.

    :param typ: Type to cast iterable to
    :param value: String value to parse as iterable
    :return: Given type
    """
    return typ(parse_str(v) for v in value.split(","))


def iterable_parser(type_: Type[IT]) -> Callable[[str], IT]:
    def _parser(value: str) -> IT:
        return parse_iterable(type_, value)

    _parser.__name__ = f"{type_}_parser"
    return _parser


parse_tuple = iterable_parser(tuple)
parse_list = iterable_parser(list)
parse_set = iterable_parser(set)
parse_frozenset = iterable_parser(frozenset)

parsers: Mapping[Type, Callable] = {
    str: parse_str,
    bool: parse_bool,
    int: parse_int,
    tuple: parse_tuple,
    list: parse_list,
    set: parse_set,
    frozenset: parse_frozenset,
}

T = TypeVar("T", bound=Any)


def get_parser(typ: Type[T]) -> Callable[[str], T]:
    """
    Return appropriate parser for given type.

    :param typ: Type to get parser for.
    :return function: Parser
    """
    try:
        return parsers[typ]
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
    settings: Dict[str, Any] = {}
    prefix = environ.get("DJANGO_SETTINGS_PREFIX", "DJANGO_")

    for key, value in environ.items():
        _, _, key = key.partition(prefix)

        if not key:
            continue

        if key in UNSUPPORTED_ENV_SETTINGS:
            raise ValueError(
                'Django setting "{}" can not be '
                "configured through environment.".format(key)
            )

        default_value = getattr(global_settings, key, UNDEFINED)

        if isinstance(default_value, Undefined):
            settings[key] = value
            continue

        parser = (
            # Handle typed django settings defaulting to None
            get_parser(SETTINGS_TYPES[key])
            if default_value is None and key in SETTINGS_TYPES.keys()
            # Determine parser by django setting type
            else get_parser(type(default_value))
        )

        settings[key] = parser(value)

    return settings


class EnvironWrapper:
    """Wrapper around os environ with type conversion support."""

    __delitem__ = environ.__delitem__
    __getitem__ = environ.__getitem__
    __setitem__ = environ.__setitem__
    __contains__ = environ.__contains__

    def __getattr__(self, item):
        return getattr(environ, item)

    TT = TypeVar("TT")
    DT = TypeVar("DT")

    @staticmethod
    def parse(parser: Callable[[str], TT], key: str, default: DT) -> Union[DT, TT]:
        value = environ.get(key, UNDEFINED)
        if isinstance(value, Undefined):
            return default
        try:
            return parser(value)
        except ValueError:
            log.warning(
                "Unable to parse environment variable {key}={value}".format(
                    key=key, value=value
                )
            )
            return default

    def get_bool(self, key: str, default: Optional[DT] = None) -> Union[bool, DT, None]:
        return self.parse(parse_bool, key, default=default)

    def get_int(self, key: str, default: Optional[DT] = None) -> Union[int, DT, None]:
        return self.parse(parse_int, key, default=default)

    def get_tuple(
        self, key: str, default: Optional[DT] = None
    ) -> Union[tuple, DT, None]:
        return self.parse(parse_tuple, key, default=default)

    def get_list(self, key: str, default: Optional[DT] = None) -> Union[list, DT, None]:
        return self.parse(parse_list, key, default=default)

    def get_set(self, key: str, default: Optional[DT] = None) -> Union[set, DT, None]:
        return self.parse(parse_set, key, default=default)

    def get_str(self, key: str, default: Optional[DT] = None) -> Union[str, DT, None]:
        return self.parse(parse_str, key, default=default)


env: Final = EnvironWrapper()


class SafeEnvironWrapper:
    """Wrapper around os.environ with strict type conversions"""

    __delitem__ = environ.__delitem__
    __getitem__ = environ.__getitem__
    __setitem__ = environ.__setitem__
    __contains__ = environ.__contains__

    def __getattr__(self, item):
        return getattr(environ, item)

    TT = TypeVar("TT", bound=Any)
    DT = TypeVar("DT", bound=Any)

    @overload
    @staticmethod
    def take(type_: Type[TT], key: str, default: Undefined) -> TT:
        ...

    @overload
    @staticmethod
    def take(type_: Type[TT], key: str, default: DT) -> Union[TT, DT]:
        ...

    @staticmethod
    def take(type_, key, default=UNDEFINED):
        parser = get_parser(type_)
        value = environ.get(key, default)
        if isinstance(value, Undefined):
            raise AttributeError(
                f"No env var named {key} found, and no default provided"
            )
        return parser(value)


safe_env: Final = SafeEnvironWrapper()
