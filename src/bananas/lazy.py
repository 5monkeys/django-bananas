from django.utils.functional import lazy

lazy_title = lazy(lambda s: s.title(), str)
lazy_capitalize = lazy(lambda s: s.capitalize(), str)
