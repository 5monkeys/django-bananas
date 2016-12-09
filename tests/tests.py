from os import environ

from django.conf import global_settings
from django.test import TestCase

from bananas import environment
from bananas.environment import env
from bananas.query import ModelDict
from .models import (
    Parent, Child, TestUUIDModel, SecretModel, URLSecretModel, Node, Simple
)

class QuerySetTest(TestCase):

    def setUp(self):
        self.simple = Simple.objects.create(name='S')
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

    def test_wrong_path(self):
        self.assertRaises(AttributeError,
                          lambda: ModelDict.from_model(self.child,
                                                       'does__not__exist'))

    def test_attribute_error(self):
        self.assertRaises(ValueError, ModelDict.from_model, self.parent,
                          test='attribute_error')

    def test_dicts(self):
        self.assertTrue(hasattr(Parent.objects, 'dicts'))

        simple = Simple.objects.all().dicts('name').first()
        self.assertEqual(simple.name, self.simple.name)

        child = Child.objects.dicts('name', 'parent__name').first()
        self.assertEqual(child.name, self.child.name)
        self.assertNotIn('parent', child)
        self.assertEqual(child.parent.name, self.parent.name)

    def test_dicts_rename(self):
        self.assertTrue(hasattr(Parent.objects, 'dicts'))

        simple = Simple.objects.all().dicts('name').first()
        self.assertEqual(simple.name, self.simple.name)

        child = Child.objects.dicts('name', parent='parent__name').order_by('name').first()
        self.assertEqual(child.name, self.child.name)
        self.assertEqual(child.parent, self.parent.name)

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


class EnvTest(TestCase):

    def test_parse_bool(self):
        self.assertTrue(environment.parse_bool('True'))
        self.assertTrue(environment.parse_bool('true'))
        self.assertTrue(environment.parse_bool('TRUE'))
        self.assertTrue(environment.parse_bool('yes'))
        self.assertTrue(environment.parse_bool('1'))
        self.assertFalse(environment.parse_bool('False'))
        self.assertFalse(environment.parse_bool('0'))
        self.assertRaises(ValueError, environment.parse_bool, 'foo')

    def test_parse_int(self):
        self.assertEqual(environment.parse_int('123'), 123)
        self.assertEqual(environment.parse_int('0644'), 420)
        self.assertEqual(environment.parse_int('0o644'), 420)

    def test_parse_tuple(self):
        self.assertTupleEqual(environment.parse_tuple('a'), ('a',))
        self.assertTupleEqual(environment.parse_tuple(' a,b, c '),
                              ('a', 'b', 'c'))

    def test_parse_list(self):
        self.assertListEqual(environment.parse_list('a, b, c'), ['a', 'b', 'c'])

    def test_parse_set(self):
        self.assertSetEqual(environment.parse_set('b, a, c'), {'a', 'b', 'c'})

    def test_env_wrapper(self):
        self.assertEqual(env.get('foo', 'bar'), 'bar')

        self.assertEqual(env.get('foo', 'bar'), 'bar')

        self.assertIsNone(env.get_bool('foobar'))

        self.assertFalse(env.get_bool('foobar', False))
        environ['foobar'] = 'True'
        self.assertTrue(env.get_bool('foobar', False))
        environ['foobar'] = 'Ture'
        self.assertIsNone(env.get_bool('foobar'))
        self.assertFalse(env.get_bool('foobar', False))

        environ['foobar'] = '123'
        self.assertEqual(env.get_int('foobar'), 123)

        environ['foobar'] = 'a, b, c'
        self.assertTupleEqual(env.get_tuple('foobar'), ('a', 'b', 'c'))

        environ['foobar'] = 'a, b, c'
        self.assertListEqual(env.get_list('foobar'), ['a', 'b', 'c'])

        environ['foobar'] = 'a, b, c'
        self.assertSetEqual(env.get_set('foobar'), {'a', 'b', 'c'})
        self.assertEqual(env.get('foobar'), 'a, b, c')
        self.assertEqual(env['foobar'], 'a, b, c')


class SettingsTest(TestCase):

    def test_module(self):
        environ.pop('DJANGO_ADMINS', None)
        environ.update({
            'DJANGO_DEBUG': 'true',
            'DJANGO_INTERNAL_IPS': '127.0.0.1, 10.0.0.1',
            'DJANGO_FILE_UPLOAD_PERMISSIONS': '0o644',
        })

        from . import settings_example as settings

        self.assertEqual(global_settings.DEBUG, False)
        self.assertEqual(settings.DEBUG, True)
        self.assertTupleEqual(settings.INTERNAL_IPS, ('127.0.0.1', '10.0.0.1'))
        self.assertIsNone(global_settings.FILE_UPLOAD_PERMISSIONS)
        self.assertEqual(settings.FILE_UPLOAD_PERMISSIONS, 420)

    def test_get_settings(self):
        environ['DJANGO_ADMINS'] = 'foobar'
        self.assertRaises(ValueError, environment.get_settings)
