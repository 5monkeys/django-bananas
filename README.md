# Django Bananas
*Django extensions the monkey way*

``` sh
$ pip install django-bananas
```

``` py
class Book(TimeStampedModel):
    author = ForeignKey(Author)
    objects = Manager.from_queryset(ExtendedValuesQuerySet)()


>>> book = Book.objects.values('id', author='author__name').first()
{'id': 1, 'author': 'Jonas'}
```
