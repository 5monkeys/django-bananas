================================================================================
:banana: Django Bananas - Django extensions the monkey way
================================================================================

.. image:: https://github.com/5monkeys/django-bananas/workflows/CI/badge.svg
  :target: https://github.com/5monkeys/django-bananas/actions

.. image:: https://img.shields.io/pypi/v/django-bananas.svg
  :target: https://pypi.python.org/pypi/django-bananas/

--------------------------------------------------------------------------------
 Install
--------------------------------------------------------------------------------

django-bananas is on PyPI, so just run:

.. code-block:: bash

    python3 -m pip install django-bananas

Using DRF specific features like Bananas Admin and fencing requires
djangorestframework and drf-yasg and it's recommended to install django-bananas
with the ``drf`` extra to keep those in sync:

.. code-block:: bash

    python3 -m pip install django-bananas[drf]

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Compatibility
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Currently tested only for

-   Django 3.2 under Python 3.8-3.10
-   Django 4.0 under Python 3.8-3.10
-   Django 4.1 under Python 3.8-3.13
-   Django 4.2 under Python 3.8-3.13
-   Django 5.0 under Python 3.10-3.13
-   Django 5.1 under Python 3.10-3.13
-   Django 5.2 under Python 3.10-3.13

Pull requests welcome!

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

.. code-block:: pycon

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

.. code-block:: pycon

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

.. code-block:: pycon

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

.. code-block:: pycon

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

.. code-block:: pycon

    >>> book = Book.objects.dicts("id", author="author__name").first()
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
        "bananas",  # Needs to be before "django.contrib.admin"
        "django.contrib.admin",
        ...,
    )

    ADMIN = {
        "SITE_HEADER": "Bananas",
        "SITE_TITLE": "Bananas Admin",
        "INDEX_TITLE": "Admin Panel",
        # 'BACKGROUND_COLOR': '#363c3f',
    }

.. code-block:: py

    # your main urls.py
    from bananas import admin

    urlpatterns = [
        # ...
        url(r"^admin/", include(admin.site.urls)),
    ]

.. code-block:: py

    # app/admin.py or something
    from django.conf.urls import url
    from bananas import admin


    @admin.register
    class MyAdminView(admin.AdminView):
        def get_urls(self):
            return [
                url(r"^custom/$", self.admin_view(self.custom_view)),
                # ^^ Note that the view is wrapped in self.admin_view.
                # Needed for permissions and to prevent any
                # threading issues.
            ]

        def get(self, request):
            return self.render("admin/template.html", {})

        def custom_view(self, request):
            return self.render("admin/custom.html", {})


++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Admin API
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Django admin API for use with `django-bananas.js
<https://github.com/5monkeys/django-bananas.js/>`_ (react admin site). This
feature requires installation with the ``drf`` extra.

.. code-block:: py

    # app/admin.py or something
    from bananas.admin.api.mixins import BananasAPI
    from bananas.admin.api.schemas import schema
    from bananas.admin.api.views import BananasAdminAPI
    from bananas.lazy import lazy_title
    from django.utils.translation import gettext_lazy as _
    from rest_framework import viewsets


    class CustomAdminAPI(BananasAdminAPI):
        name = lazy_title(_("custom"))

        @schema(query_serializer=SomeSerializer, responses={200: SomeSerializer})
        def list(self, request):
            return ...


    class SomeModelAdminAPI(BananasAPI, viewsets.ModelViewSet):
        serializer_class = SomeModelSerializer

        def list(self, request):
            return ...

.. code-block:: py

    # app/urls.py or something
    from bananas.admin import api
    from django.conf.urls import include, path

    from .admin import CustomAdminAPI, SomeModelAdminAPI

    api.register(CustomAdminAPI)
    api.register(SomeModelAdminAPI)

    urlpatterns = [
        path(r"^api/", include("bananas.admin.api.urls")),
    ]

.. code-block:: py

   # setting.py
   ADMIN = {
       "API": {
           # Optional: override the default OpenAPI schemes
           "SCHEMES": ["https"],
       }
   }


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
 mysqlgis                       django.contrib.gis.db.backends.mysql
 oraclegis                      django.contrib.gis.db.backends.oracle
 postgis                        django.contrib.gis.db.backends.postgis
 spatialite                     django.contrib.gis.db.backends.spatialite
==============================  ===========================================

You can add your own by running ``register(scheme, module_name)`` before parsing.

database_conf_from_url(url)
  Return a django-style database configuration based on ``url``.

  :param url: Database URL
  :return: Django-style database configuration dict

  Example:

  .. code-block:: pycon

      >>> from bananas.url import database_conf_from_url
      >>> conf = database_conf_from_url(
      ...     "pgsql://joar:hunter2@5monkeys.se:4242/tweets/tweetschema?hello=world"
      ... )
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

    .. code-block:: pycon

        >>> # env ONE=1
        >>> env.get_int("ONE")
        1
        >>> env.get_int("TWO")  # Not set
        None
        >>> env.get_int("TWO", -1)  # Not set, default to -1
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

    .. code-block:: pycon

        >>> # env CAN_DO=1 NO_THANKS=false NO_HABLA=f4lse
        >>> env.get_bool("CAN_DO")
        True
        >>> env.get_bool("NO_THANKS")
        False
        >>> env.get_bool("NO_HABLA")  # Set, but not valid
        None
        >>> env.get_bool("NO_HABLA", True)  # Set, but not valid, with default
        True
        >>> env.get_bool("IS_NONE")  # Not set
        None
        >>> env.get_bool("IS_NONE", False)  # Not set, default provided
        False


:get_tuple, get_list, get_set:

    Returns a ``tuple``, ``list`` or ``set`` of the environment variable string,
    split by the ascii comma character. e.g.:

    .. code-block:: pycon

        >>> # env FOOS=foo,foo,bar
        >>> get_list("FOO")
        ['foo', 'foo', 'bar']
        >>> get_set("FOO")
        set(['foo', 'bar'])

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
bananas.secrets - Helpers for getting secrets from files
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Is useful for getting the content of secrets stored in files. One usecase is `docker secrets
<https://docs.docker.com/engine/swarm/secrets/>`_.

``BANANAS_SECRETS_DIR`` can be used to configure the directory that secrets live in. Defaults to ``/run/secrets/``.

.. code-block:: pycon

    >>> from bananas import secrets

    >>> secrets.get_secret("hemlis")
    "topsecret"

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
bananas.drf.fencing - Fence DRF views with HTTP conditional headers
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Building blocks for composing HTTP conditionals to guard DRF views. Built to
work well in conjunction with ``BananasAdminAPI`` and ``TimeStampedModel``. This
feature requires installation with the ``drf`` extra.

Fences add a header parameter to the exposed OpenAPI schema if you're using
drf-yasg.

``allow_if_unmodified_since``
=============================

Make a view-set for a ``TimeStampedModel`` only accept updates when
``If-Unmodified-Since`` specifies a date before the ``date_modified`` of the
updated instance.

Due to comparing datetime instances, using ``allow_if_unmodified_since``
requires running Django with timezone support enabled, ``USE_TZ = TRUE``.

.. code-block:: python

    from bananas.drf.fencing import FencedUpdateModelMixin, allow_if_unmodified_since


    class ItemAPI(FencedUpdateModelMixin, GenericViewSet):
        fence = allow_if_unmodified_since()
        serializer_class = ItemSerializer

``allow_if_match``
==================

Make a view-set that requires passing a version string in ``If-Match`` and
rejects requests when the given version does not match the ``version`` attribute
of the updated instance.

.. code-block:: python

    from bananas.drf.fencing import FencedUpdateModelMixin, allow_if_match


    class ItemAPI(FencedUpdateModelMixin, GenericViewSet):
        fence = allow_if_match(operator.attrgetter("version"))
        serializer_class = ItemSerializer

``Fence``
=========

Example implementing a fence for ``If-Modified-Since``:

.. code-block:: python

    import operator
    from drf_yasg import openapi
    from rest_framework import status
    from rest_framework.exceptions import APIException
    from bananas.drf.fencing import Fence, header_date_parser, parse_date_modified


    class NotModified(APIException):
        status_code = status.HTTP_304_NOT_MODIFIED
        default_detail = "An HTTP precondition failed"
        default_code = "not_modified"


    allow_if_not_modified_since = Fence(
        get_token=header_date_parser("If-Modified-Since"),
        compare=operator.gt,
        get_version=parse_date_modified,
        openapi_parameter=openapi.Parameter(
            in_=openapi.IN_HEADER,
            name="If-Modified-Since",
            type=openapi.TYPE_STRING,
            required=True,
            description=(
                "Time of last edit of the client's representation of the resource in "
                "RFC7231 format."
            ),
        ),
        rejection=NotModified("The resource is unmodified"),
    )

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Contributing
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Contributing is welcome in the form of PRs and issues. If you want to add a
bigger feature or contribute with a large change in current behaviour it's
always a good idea to start a discussion with an issue before getting started.

New additions will be expected to have 100% test coverage as well as type hints
and documentation to be considered to be merged.

Development
===========

Testing and development requirements can be installed using package extras
``test`` and ``dev`` respectively. You'll most likely always want to install the
``drf`` extra when installing ``dev``.

To get started, setup a virtualenv and then install test requirements and run
tests and checks on Python 3.9/Django 3.1 with:

.. code-block:: bash

    python3 -m pip install -e .[test]
    TOXENV=py39-django31,checks python3 -m tox

You can install development requirements into your virtualenv. Linting and
formatting uses pre-commit which you could also install on a system level.

.. code-block:: bash

    python3 -m pip install -e .[dev,drf]
    make type-check
    pre-commit run --all-files

After installing pre-commit, you can enable hooks to have it run before you
publish pull requests.

.. code-block:: bash

    pre-commit install -t pre-push

After installing ``dev`` you can also run tests without tox for rapid iteration
and select specific tests with the ``test`` argument to ``make test``:

.. code-block:: bash

    make test test='-k test_logout'
