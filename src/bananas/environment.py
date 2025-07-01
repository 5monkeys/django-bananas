import logging
from functools import partial
from os import environ
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    Generic,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from django.conf import global_settings
from typing_extensions import Protocol, overload

__all__ = ["env", "parse_bool", "parse_int", "parse_tuple", "parse_list", "parse_set"]


log = logging.getLogger(__name__)


class Undefined: ...


UNDEFINED: Final = Undefined()

UNSUPPORTED_ENV_SETTINGS = (
    "ADMINS",
    "MANAGERS",
    "LANGUAGES",
    "DISALLOWED_USER_AGENTS",
    "IGNORABLE_404_URLS",
    "TEMPLATES",
)

SETTINGS_TYPES: Dict[str, type] = {
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
    else:
        raise ValueError(f'Unable to parse boolean value "{value}"')


def parse_int(value: str) -> int:
    """
    Parse numeric string to int. Supports oct formatted string.

    :param str value: String value to parse as int
    :return int:
    """
    value = parse_str(value=value)
    if value != "0" and value.startswith("0"):
        return int(value.lstrip("0o"), 8)
    else:
        return int(value)


Q = TypeVar("Q", covariant=True)


class _Instantiable(Protocol[Q]):
    def __init__(self, value: Iterable[Q]) -> None: ...


class _InstantiableIterable(Iterable[Q], _Instantiable[Q], Generic[Q]): ...


T = TypeVar("T", bound=_InstantiableIterable)


def parse_iterable(typ: Type[T], value: str) -> T:
    """
    Parse comma separated string into typed iterable.

    :param typ: Type to cast iterable to
    :param value: String value to parse as iterable
    :return: Given type
    """
    return typ(parse_str(v) for v in value.split(","))


parse_tuple = cast(Callable[[str], Tuple[str, ...]], partial(parse_iterable, tuple))
parse_list = cast(Callable[[str], List[str]], partial(parse_iterable, list))
parse_set = cast(Callable[[str], Set[str]], partial(parse_iterable, set))


Builtin = Union[str, bool, int]
B = TypeVar("B", bound=Builtin)
P = TypeVar("P", bound=Union[Builtin, tuple, list, set])


@overload
def get_parser(typ: Type[B]) -> Callable[[str], B]: ...


@overload
def get_parser(typ: Type[tuple]) -> Callable[[str], Tuple[str, ...]]: ...


@overload
def get_parser(typ: Type[list]) -> Callable[[str], List[str]]: ...


@overload
def get_parser(typ: Type[set]) -> Callable[[str], Set[str]]: ...


def get_parser(typ: Type[P]) -> Callable[[str], P]:
    """
    Return appropriate parser for given type.

    :param typ: Type to get parser for.
    :return function: Parser
    """
    try:
        return cast(
            Callable[[str], P],
            {
                str: parse_str,
                bool: parse_bool,
                int: parse_int,
                tuple: parse_tuple,
                list: parse_list,
                set: parse_set,
            }[typ],
        )
    except KeyError as exc:
        raise NotImplementedError("Unsupported setting type: %r", typ) from exc


def get_settings() -> Dict[str, Any]:
    """
    Get and parse prefixed django settings from env.

    TODO: Implement support for complex settings
        DATABASES = {}
        CACHES = {}
        INSTALLED_APPS -> EXCLUDE_APPS ?

    :return dict:
    """
    settings = {}
    prefix = environ.get("DJANGO_SETTINGS_PREFIX", "DJANGO_")
    parse: Callable[[str], object]

    for key, value in environ.items():
        _, _, key = key.partition(prefix)
        if key:
            if key in UNSUPPORTED_ENV_SETTINGS:
                raise ValueError(
                    f'Django setting "{key}" can not be '
                    "configured through environment."
                )

            default_value = getattr(global_settings, key, UNDEFINED)

            if default_value is not UNDEFINED:
                if default_value is None and key in SETTINGS_TYPES.keys():
                    # Handle typed django settings defaulting to None
                    parse = get_parser(SETTINGS_TYPES[key])
                else:
                    # Determine parser by django setting type
                    parse = get_parser(type(default_value))  # type: ignore[type-var]

                value = parse(value)  # type: ignore[assignment]

            settings[key] = value

    return settings


S = TypeVar("S")
U = TypeVar("U")


class EnvironWrapper:
    """
    Wrapper around os environ with type conversion support.
    """

    def __delitem__(self, key: str) -> None:
        environ.__delitem__(key)

    def __getitem__(self, key: str) -> str:
        return environ.__getitem__(key)

    def __setitem__(self, key: str, value: str) -> None:
        environ.__setitem__(key, value)

    def __contains__(self, key: object) -> bool:
        return environ.__contains__(key)

    def __getattr__(self, item: str) -> object:
        return getattr(environ, item)

    get: Callable[..., str]

    @overload
    def parse(
        self, parser: Callable[[str], S], key: str, default: None
    ) -> Optional[S]: ...

    @overload
    def parse(self, parser: Callable[[str], S], key: str, default: S) -> S: ...

    def parse(
        self, parser: Callable[[str], S], key: str, default: Optional[S] = None
    ) -> Optional[S]:
        value: Union[str, Undefined] = environ.get(key, UNDEFINED)
        if isinstance(value, Undefined):
            return default
        try:
            return parser(value)
        except ValueError:
            log.warning(f"Unable to parse environment variable {key}={value}")
            return default

    @overload
    def get_bool(self, key: str, default: U) -> Union[bool, U]: ...

    @overload
    def get_bool(self, key: str, default: None = None) -> Optional[bool]: ...

    def get_bool(self, key: str, default: object = None) -> object:
        return self.parse(parse_bool, key, default=default)

    @overload
    def get_int(self, key: str, default: U) -> Union[int, U]: ...

    @overload
    def get_int(self, key: str, default: None = None) -> Optional[int]: ...

    def get_int(self, key: str, default: object = None) -> object:
        return self.parse(parse_int, key, default=default)

    @overload
    def get_tuple(self, key: str, default: U) -> Union[Tuple[str, ...], U]: ...

    @overload
    def get_tuple(
        self, key: str, default: None = None
    ) -> Optional[Tuple[str, ...]]: ...

    def get_tuple(self, key: str, default: object = None) -> object:
        return self.parse(parse_tuple, key, default=default)

    @overload
    def get_list(self, key: str, default: U) -> Union[List[str], U]: ...

    @overload
    def get_list(self, key: str, default: None = None) -> Optional[List[str]]: ...

    def get_list(self, key: str, default: object = None) -> object:
        return self.parse(parse_list, key, default=default)

    @overload
    def get_set(self, key: str, default: U) -> Union[Set[str], U]: ...

    @overload
    def get_set(self, key: str, default: None = None) -> Optional[Set[str]]: ...

    def get_set(self, key: str, default: object = None) -> object:
        return self.parse(parse_set, key, default=default)


env = EnvironWrapper()
