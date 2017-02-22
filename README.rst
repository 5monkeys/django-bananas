================================================================================
:banana: Django Bananas - Django extensions the monkey way
================================================================================

.. image:: https://api.travis-ci.org/5monkeys/django-bananas.svg?branch=master
  :target: https://travis-ci.org/5monkeys/django-bananas?branch=master

.. image:: https://coveralls.io/repos/5monkeys/django-bananas/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/5monkeys/django-bananas?branch=master

.. image:: https://img.shields.io/pypi/v/django-bananas.svg
  :target: https://pypi.python.org/pypi/django-bananas/

--------------------------------------------------------------------------------
 Install
--------------------------------------------------------------------------------

django-bananas is on PyPI, so just run:

.. code-block:: bash

    pip install django-bananas

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Compatibility
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Currently tested only for

-   Django 1.8-1.11b1 under Python 3.4-3.6

pull requests welcome!

--------------------------------------------------------------------------------
 Examples
--------------------------------------------------------------------------------

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Models
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

TimeStampedModel
================================================================================

Abstract ``TimeStampedModel`` with date created/modified fields:

Use TimeStampedModel as base class for your model

.. code-block:: py

    from bananas.models import TimeStampedModel

    class Book(TimeStampedModel):
        pass


the timestamps can be accessed on the model as

.. code-block:: py

    >>> book.date_created
    >>> book.date_modified


UUIDModel
================================================================================

Abstract model that uses a Django 1.8 UUID field as the primary key.

.. code-block:: py

    from bananas.models import UUIDModel

    class User(UUIDModel):
        display_name = models.CharField(max_length=255)
        email = models.EmailField()

    >>> user.id
    UUID('70cf1f46-2c79-4fc9-8cc8-523d67484182')

    >>> user.pk
    UUID('70cf1f46-2c79-4fc9-8cc8-523d67484182')

SecretField
================================================================================

Can be used to generate and store "safe" random bytes for authentication.

.. code-block:: py

    from bananas.models import SecretField

    class User(models.Model):
        # Ask for 32 bytes and require 24 bytes from urandom
        token = SecretField(num_bytes=32, min_bytes=24)

    >>> User.objects.create()  # Token is generated automatically
    >>> user.token
    '3076f884da827809e80ced236e8da20fa36d0c27dd036bdd4afbac34807e5cf1'



URLSecretField
================================================================================

An implementation of SecretField that generates an URL-safe base64 string 
instead of a hex representation of the random bytes.


.. code-block:: py

    from bananas.models import URLSecretField


    class User(models.Model):
        # Generates an URL-safe base64 representation of the random value
        token = URLSecretField(num_bytes=32, min_bytes=24)

    >>> user.token
    'WOgrNwqFKOF_LsHorJy_hGpPepjvVH7Uar-4Z_K6DzU-'


++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 ORM
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

New ``queryset.dicts()`` with field renaming through kwargs, and `dot-dict`
style results:

.. code-block:: py

    from bananas.query import ExtendedQuerySet

    class Book(TimeStampedModel):
        author = ForeignKey(Author)
        objects = Manager.from_queryset(ExtendedQuerySet)()

    >>> book = Book.objects.dicts('id', author='author__name').first()
    {'id': 1, 'author': 'Jonas'}
    >>> book.author
    'Jonas'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Admin
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Custom django admin stylesheet.

.. warning:: Work in progress. Only a few views styled completely as of now.

.. code-block:: py

    # settings.py
    INSTALLED_APPS = (
        'bananas',  # Needs to be before 'django.contrib.admin'
        'django.contrib.admin',
        ...
    )

    ADMIN = {
        'SITE_HEADER': 'Bananas',
        'SITE_TITLE': 'Bananas Admin',
        'INDEX_TITLE': 'Admin Panel',
        # 'BACKGROUND_COLOR': '#363c3f',
    }

.. code-block:: py

    # your main urls.py
    from bananas import admin

    urlpatterns = [
        ...
        url(r'^admin/', include(admin.site.urls)),
    ]


++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Database URLs
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Parse database information from a URL, kind of like SQLAlchemy.

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

You can add your own by running ``register(scheme, module_name)`` before parsing.

database_conf_from_url(url)
  Return a django-style database configuration based on ``url``.

  :param url: Database URL
  :return: Django-style database configuration dict

  Example:

  .. code-block:: py

      >>> from bananas.url import database_conf_from_url
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


++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
bananas.environment - Helpers to get setting values from environment variables
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

``bananas.environment.env`` is a wrapper around ``os.environ``, it provides the
standard ``.get(key, value)``, method to get a value for a key, or a default if
the key is not set - by default that default is ``None`` as you would expect.
What is more useful is the additional type-parsing ``.get_*`` methods it
provides:

-   ``get_bool``
-   ``get_int``
-   ``get_list``, ``get_set``, ``get_tuple``


:get_int:

    .. code-block:: python

        >>> # env ONE=1
        >>> env.get_int('ONE')
        1
        >>> env.get_int('TWO')  # Not set
        None
        >>> env.get_int('TWO', -1)  # Not set, default to -1
        -1


:get_bool:
    returns ``True`` if the environment variable value is any of,
    case-insensitive:

    -   ``"true"``
    -   ``"yes"``
    -   ``"on"``
    -   ``"1"``

    returns ``False`` if the environment variable value is any of,
    case-insensitive:

    -   ``"false"``
    -   ``"no"``
    -   ``"off"``
    -   ``"0"``

    if the value is set to anything other than above, the default value will be returned instead.

    e.g.:

    .. code-block:: python

        >>> # env CAN_DO=1 NO_THANKS=false NO_HABLA=f4lse
        >>> env.get_bool('CAN_DO')
        True
        >>> env.get_bool('NO_THANKS')
        False
        >>> env.get_bool('NO_HABLA')  # Set, but not valid
        None
        >>> env.get_bool('NO_HABLA', True)  # Set, but not valid, with default
        True
        >>> env.get_bool('IS_NONE')  # Not set
        None
        >>> env.get_bool('IS_NONE', False)  # Not set, default provided
        False


:get_tuple, get_list, get_set:

    Returns a ``tuple``, ``list`` or ``set`` of the environment variable string,
    split by the ascii comma character. e.g.:

    .. code-block:: python

        >>> # env FOOS=foo,foo,bar
        >>> get_list('FOO')
        ['foo', 'foo', 'bar']
        >>> get_set('FOO')
        set(['foo', 'bar'])
