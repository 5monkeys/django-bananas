# :banana: Django Bananas
*Django extensions the monkey way*

### Install
``` sh
$ pip install django-bananas
```

> **Note:** Currently bleeding edge, only tested in *Python 3.4* / *Django 1.8*, pull requests welcomed.

### Examples

#### Models
Abstract `TimeStampedModel` with date created/modified fields:
``` py
class Book(TimeStampedModel):
    pass

book.date_created
book.date_modified
```

#### ORM
New `queryset.dicts()` with field renaming through kwargs, and *dot-dict* style results:
``` py
class Book(TimeStampedModel):
    author = ForeignKey(Author)
    objects = Manager.from_queryset(ExtendedQuerySet)()

>>> book = Book.objects.dicts('id', author='author__name').first()
{'id': 1, 'author': 'Jonas'}
>>> book.author
'Jonas'
```

#### Admin
Custom django admin stylesheet.

> **Note:** Work-in-progress! Only a few views styled and not tested cross-browser.

``` py
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
```

``` py
# urls.py
from bananas import admin

urlpatterns = [
    ...
    url(r'^admin/', include(admin.site.urls)),
]
```
