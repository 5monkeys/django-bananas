from django.test import TestCase
from .models import Parent, Child


class QuerySetTest(TestCase):

    def setUp(self):
        parent = Parent.objects.create()
        Child.objects.create(parent=parent)

    def test_dicts(self):
        self.assertTrue(hasattr(Parent.objects, 'dicts'))
        parent = Parent.objects.dicts('id', 'child__date_created').first()
        self.assertIsNotNone(parent.id)
