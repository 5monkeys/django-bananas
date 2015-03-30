# :banana: Django Bananas
*Django extensions the monkey way*

### Install
``` sh
$ pip install django-bananas
```

> **Note:** Currently bleeding edge, only tested in *Python 3.4* / *Django 1.8*, pull requests welcomed.

### Examples

Abstract `TimeStampedModel` with date created/modified fields:
``` py
class Book(TimeStampedModel):
    pass

book.date_created
book.date_modified
```

Extended `queryset.values()` with field renaming through kwargs, and *dot-dict* style results:
``` py
class Book(TimeStampedModel):
    author = ForeignKey(Author)
    objects = Manager.from_queryset(ExtendedValuesQuerySet)()

>>> book = Book.objects.values('id', author='author__name').first()
{'id': 1, 'author': 'Jonas'}
>>> book.author
'Jonas'
```
