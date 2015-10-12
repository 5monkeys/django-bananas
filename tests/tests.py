from django.test import TestCase
from bananas.query import ModelDict
from .models import Parent, Child, TestUUIDModel, SecretModel, URLSecretModel,\
    Node


class QuerySetTest(TestCase):

    def setUp(self):
        self.parent = Parent.objects.create(name='A')
        self.child = Child.objects.create(name='B', parent=self.parent)

    def test_modeldict(self):
        d = ModelDict(foo='bar', baz__ham='spam')
        self.assertIn('foo', d, 'should have key "foo"')
        self.assertNotIn('baz', d, 'should not have key "baz"')
        self.assertRaises(AttributeError, d.__getattr__, 'x')
        self.assertTrue(hasattr(d, 'foo'), 'should not have real attr "foo"')
        self.assertEqual(d.foo, 'bar')
        self.assertEqual(d.baz__ham, 'spam')
        self.assertIsInstance(d.baz, ModelDict, 'should lazy resolve sub dict')

    def test_modeldict_from_model(self):
        d = ModelDict.from_model(self.child, 'id', 'parent__id', 'parent__name')
        self.assertDictEqual(d, {
            'id': self.child.id,
            'parent__id': self.parent.id,
            'parent__name': 'A'
        })
        self.assertTrue(d.parent)

        _child = Child.objects.create(name='B')
        d = ModelDict.from_model(_child, 'id', 'parent__id', 'parent__name')
        self.assertDictEqual(d, {
            'id': _child.id,
            'parent': None,
        })

        _parent = Node.objects.create(name='A', parent=None)
        _child = Node.objects.create(name='B', parent=_parent)
        _grandchild = Node.objects.create(name='C', parent=_child)

        d = ModelDict.from_model(_grandchild,
                                 test__id='parent__parent__id',
                                 test__name='parent__parent__name')
        self.assertDictEqual(d, {
            'test__id': self.parent.id,
            'test__name': 'A',
        })
        self.assertDictEqual(d.test, {
            'id': self.parent.id,
            'name': 'A',
        })

        _child.parent = None
        _child.save()

        d = ModelDict.from_model(_grandchild,
                                 test__id='parent__parent__id',
                                 test__name='parent__parent__name')
        self.assertDictEqual(d, {
            'test__id': None,
            'test__name': None,
        })


    def test_dicts(self):
        self.assertTrue(hasattr(Parent.objects, 'dicts'))

        child = Child.objects.dicts('name', 'parent__name').first()
        self.assertEqual(child.name, self.child.name)
        self.assertNotIn('parent', child)
        self.assertEqual(child.parent.name, self.parent.name)

    def test_uuid_model(self):
        first = TestUUIDModel.objects.create(text='first')

        second = TestUUIDModel.objects.create(text='second',
                                              parent=first)

        self.assertEqual(TestUUIDModel.objects.get(parent=first), second)
        self.assertEqual(TestUUIDModel.objects.get(parent__pk=first.pk),
                         second)

    def test_secret_field(self):
        model = SecretModel.objects.create()

        field = SecretModel._meta.get_field('secret')

        field_length = field.get_field_length(field.num_bytes)

        self.assertEqual(len(model.secret), field_length)

    def test_url_secret_field_field_length(self):
        model = URLSecretModel.objects.create()

        field = URLSecretModel._meta.get_field('secret')

        field_length = field.get_field_length(field.num_bytes)

        # secret value may be shorter
        self.assertLessEqual(len(model.secret), field_length)

    def test_url_secret_field_is_safe(self):
        model = URLSecretModel.objects.create()

        self.assertRegex(model.secret, r'^[A-Za-z0-9._-]+$')
