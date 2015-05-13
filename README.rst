================================================================================
:banana: Django Bananas - Django extensions the monkey way
================================================================================

--------------------------------------------------------------------------------
 Install
--------------------------------------------------------------------------------

django-bananas is on PyPI, so just run:

.. code-block:: bash

    pip install django-bananas

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Compatibility
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Currently bleeding edge, tested in

-   Django 1.8 under Python 3.4

pull requests welcome!

--------------------------------------------------------------------------------
 Examples
--------------------------------------------------------------------------------

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 Models
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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
