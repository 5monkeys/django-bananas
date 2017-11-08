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
==============================  ===========================================

You can add your own by running ``register(scheme, module_name)`` before
parsing.
"""
from collections import namedtuple
from urllib.parse import unquote_plus
from .compat import urlsplit, parse_qs


class Alias(object):
    """
    An alias object used to resolve aliases for engine names.
    """
    def __init__(self, target):
        self.target = target

    def __repr__(self):
        return '<Alias to "{}">'.format(self.target)


ENGINE_MAPPING = {
    'pgsql': Alias('postgresql'),
    'postgres': Alias('postgresql'),
    'postgresql': 'django.db.backends.postgresql_psycopg2',
    'mysql': 'django.db.backends.mysql',
    'oracle': 'django.db.backends.oracle',
    'sqlite': Alias('sqlite3'),
    'sqlite3': 'django.db.backends.sqlite3'
}


def register_engine(scheme, module):
    """
    Register a new engine.

    :param scheme: The scheme that should be matched
    :param module:
    :return:
    """
    ENGINE_MAPPING.update({scheme: module})


def resolve(cursor, key):
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

        return result
    except KeyError:
        raise KeyError('No matches for engine %s' % key)


def get_engine(scheme):
    """
    Perform a lookup in _ENGINE_MAPPING using engine_string.

    :param scheme: '+'-separated string Maximum of 2 parts,
    i.e "postgres+psycopg" is OK, "postgres+psycopg2+postgis" is NOT OK.
    :return: Engine string
    """
    path = scheme.split('+')
    first, rest = path[0], path[1:]

    second = rest[0] if rest else None

    engine = resolve(ENGINE_MAPPING, first)

    # If the selected engine does not have a second level.
    if not isinstance(engine, list):
        # If second level engine was expected
        if second:
            raise KeyError('%s has no sub-engines' % first)

        return engine

    try:
        engine, extra = engine
    except ValueError:
        # engine was not a list of length 2
        raise ValueError('django-bananas.url\' engine '
                         'configuration is invalid: %r' %
                         ENGINE_MAPPING)

    # Get second-level engine
    if second is not None:
        engine = resolve(extra, second)

    # Sanity-check the value before returning
    assert not isinstance(engine, (list, dict)), 'Only two levels of engines ' \
                                                 'are allowed'
    assert engine, 'The returned engine is not truthy'

    return engine


DatabaseInfo = namedtuple('DatabaseInfo', [
    'engine',
    'name',
    'schema',
    'user',
    'password',
    'host',
    'port',
    'params'
])


def parse_path(path):
    """
    Get database name and database schema from path.

    :param path: "/"-delimited path, parsed as
     "/<database name>/<database schema>"
    :return: tuple with (database or None, schema or None)
    """
    if path is None:
        raise ValueError('path must be a string')

    parts = path.strip('/').split('/')

    database = unquote_plus(parts[0]) if len(parts) else None
    schema = parts[1] if len(parts) > 1 else None

    return database, schema


def database_conf_from_url(url):
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
    return {key.upper(): val
            for key, val in parse_database_url(url)._asdict().items()}


def parse_database_url(url):
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
    if url == 'sqlite://:memory:':
        raise Exception('Your url is "sqlite://:memory:", if you want '
                        'an sqlite memory database, just use "sqlite://"')
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
        params=params
    )
