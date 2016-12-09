import django

if django.VERSION[0] == 1 and django.VERSION[1] < 9:
    from .django18 import ExtendedModelDictQuerySetMixin, ModelDictQuerySetMixin
else:
    from .django19 import ExtendedModelDictQuerySetMixin, ModelDictQuerySetMixin


__all__ = ['ExtendedModelDictQuerySetMixin', 'ModelDictQuerySetMixin']
