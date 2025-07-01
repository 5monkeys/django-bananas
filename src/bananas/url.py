"""
--------------------------------------------------------------------------------
 bananas.url - Create Django database configuration from database URIs
--------------------------------------------------------------------------------

Parse database information from a URL, kind of like SQLAlchemy.

================================================================================
 Engines
================================================================================

Currently supported engines are:

==============================  ===========================================
 URI scheme                     Engine
==============================  ===========================================
 pgsql, postgres, postgresql    django.db.backends.postgresql_psycopg2
 mysql                          django.db.backends.mysql
 oracle                         django.db.backends.oracle
 sqlite, sqlite3                django.db.backends.sqlite3
 mysqlgis                       django.contrib.gis.db.backends.mysql
 oraclegis                      django.contrib.gis.db.backends.oracle
 postgis                        django.contrib.gis.db.backends.postgis
 spatialite                     django.contrib.gis.db.backends.spatialite
==============================  ===========================================

You can add your own by running ``register(scheme, module_name)`` before
parsing.
"""

from typing import Any, Dict, Final, List, Mapping, NamedTuple, Optional, Tuple, Union
from urllib.parse import parse_qs, unquote_plus, urlsplit


class Alias:
    """
    An alias object used to resolve aliases for engine names.
    """

    def __init__(self, target: str) -> None:
        self.target = target

    def __repr__(self) -> str:
        return f'<Alias to "{self.target}">'


_EngineReference = Union[Alias, str, List[Union[str, Dict[str, str]]]]
ENGINE_MAPPING: Final[Dict[str, _EngineReference]] = {
    "pgsql": Alias("postgresql"),
    "postgres": Alias("postgresql"),
    "postgresql": "django.db.backends.postgresql_psycopg2",
    "mysql": "django.db.backends.mysql",
    "oracle": "django.db.backends.oracle",
    "sqlite": Alias("sqlite3"),
    "sqlite3": "django.db.backends.sqlite3",
    "mysqlgis": "django.contrib.gis.db.backends.mysql",
    "oraclegis": "django.contrib.gis.db.backends.oracle",
    "postgis": "django.contrib.gis.db.backends.postgis",
    "spatialite": "django.contrib.gis.db.backends.spatialite",
}


def register_engine(
    scheme: str,
    module: Union[Alias, str, List[Union[str, Dict[str, str]]]],
) -> None:
    """
    Register a new engine.

    :param scheme: The scheme that should be matched
    :param module:
    :return:
    """
    ENGINE_MAPPING.update({scheme: module})


def resolve(
    cursor: Mapping[str, _EngineReference], key: str
) -> Union[List[Union[str, Dict[str, str]]], str]:
    """
    Get engine or raise exception, resolves Alias-instances to a sibling target.

    :param cursor: The object so search in
    :param key: The key to get
    :return: The object found
    """
    try:
        result = cursor[key]

        # Resolve alias
        if isinstance(result, Alias):
            result = cursor[result.target]

        assert not isinstance(
            result, Alias
        ), "Multiple levels of aliases are not supported"

        return result
    except KeyError as exc:
        raise KeyError("No matches for engine %s" % key) from exc


def get_engine(scheme: str) -> str:
    """
    Perform a lookup in ENGINE_MAPPING using engine_string.

    :param scheme: '+'-separated string Maximum of 2 parts,
    i.e "postgres+psycopg" is OK, "postgres+psycopg2+postgis" is NOT OK.
    :return: Engine string
    """
    path = scheme.split("+")
    first, rest = path[0], path[1:]

    second = rest[0] if rest else None

    engine: Union[str, List[Union[str, Dict[str, str]]], Dict[str, str]]

    engine = resolve(ENGINE_MAPPING, first)

    # If the selected engine does not have a second level.
    if not isinstance(engine, list):
        # If second level engine was expected
        if second:
            raise KeyError("%s has no sub-engines" % first)

        return engine

    try:
        engine, extra = engine
    except ValueError as exc:
        # engine was not a list of length 2
        raise ValueError(
            "django-bananas.url' engine "
            "configuration is invalid: %r" % ENGINE_MAPPING
        ) from exc

    assert isinstance(
        extra, Mapping
    ), "The second element in an engine configuration must be a mapping"

    # Get second-level engine
    if second is not None:
        engine = resolve(extra, second)

    # Sanity-check the value before returning
    assert not isinstance(
        engine, (list, dict)
    ), "Only two levels of engines are allowed"
    assert engine, "The returned engine is not truthy"

    return engine


class DatabaseInfo(NamedTuple):
    engine: str
    name: Optional[str]
    schema: Optional[str]
    user: Optional[str]
    password: Optional[str]
    host: Optional[str]
    port: Optional[int]
    params: Dict[str, str]


def parse_path(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get database name and database schema from path.

    :param path: "/"-delimited path, parsed as
     "/<database name>/<database schema>"
    :return: tuple with (database or None, schema or None)
    """
    if path is None:
        raise ValueError("path must be a string")

    parts = path.strip("/").split("/")

    database = unquote_plus(parts[0]) if len(parts) else None
    schema = parts[1] if len(parts) > 1 else None

    return database, schema


def database_conf_from_url(url: str) -> Dict[str, Any]:
    """
    Return a django-style database configuration based on ``url``.

    :param url: Database URL
    :return: Django-style database configuration dict

    Example:
    >>> conf = database_conf_from_url(
    ...     'pgsql://joar:hunter2@5monkeys.se:4242/tweets/tweetschema'
    ...     '?hello=world')
    >>> sorted(conf.items())  # doctest: +NORMALIZE_WHITESPACE
    [('ENGINE', 'django.db.backends.postgresql_psycopg2'),
     ('HOST', '5monkeys.se'),
     ('NAME', 'tweets'),
     ('PARAMS', {'hello': 'world'}),
     ('PASSWORD', 'hunter2'),
     ('PORT', 4242),
     ('SCHEMA', 'tweetschema'),
     ('USER', 'joar')]
    """
    return {key.upper(): val for key, val in parse_database_url(url)._asdict().items()}


def parse_database_url(url: str) -> DatabaseInfo:
    """
    Parse a database URL and return a DatabaseInfo named tuple.

    :param url: Database URL
    :return: DatabaseInfo instance

    Example:
    >>> conf = parse_database_url(
    ...     'pgsql://joar:hunter2@5monkeys.se:4242/tweets/tweetschema'
    ...     '?hello=world')
    >>> conf  # doctest: +NORMALIZE_WHITESPACE
    DatabaseInfo(engine='django.db.backends.postgresql_psycopg2',
                 name='tweets',
                 schema='tweetschema',
                 user='joar',
                 password='hunter2',
                 host='5monkeys.se',
                 port=4242,
                 params={'hello': 'world'})
    """
    if url == "sqlite://:memory:":
        raise Exception(
            'Your url is "sqlite://:memory:", if you want '
            'an sqlite memory database, just use "sqlite://"'
        )
    url_parts = urlsplit(url)

    engine = get_engine(url_parts.scheme)
    database, schema = parse_path(url_parts.path)
    port = url_parts.port
    host = url_parts.hostname
    user = url_parts.username
    password = url_parts.password

    # Take the last element of every parameter list
    params = {key: val.pop() for key, val in parse_qs(url_parts.query).items()}

    return DatabaseInfo(
        engine=engine,
        name=database,
        schema=schema,
        user=user,
        password=password,
        host=host,
        port=port,
        params=params,
    )
