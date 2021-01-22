from os import environ
from unittest import TestCase

from bananas import environment
from bananas.environment import env


class EnvTest(TestCase):
    def test_parse_bool(self):
        self.assertTrue(environment.parse_bool("True"))
        self.assertTrue(environment.parse_bool("true"))
        self.assertTrue(environment.parse_bool("TRUE"))
        self.assertTrue(environment.parse_bool("yes"))
        self.assertTrue(environment.parse_bool("1"))
        self.assertFalse(environment.parse_bool("False"))
        self.assertFalse(environment.parse_bool("0"))
        self.assertRaises(ValueError, environment.parse_bool, "foo")

    def test_parse_int(self):
        self.assertEqual(environment.parse_int("123"), 123)
        self.assertEqual(environment.parse_int("0644"), 420)
        self.assertEqual(environment.parse_int("0o644"), 420)
        self.assertEqual(environment.parse_int("0"), 0)

    def test_parse_tuple(self):
        self.assertTupleEqual(environment.parse_tuple("a"), ("a",))
        self.assertTupleEqual(environment.parse_tuple(" a,b, c "), ("a", "b", "c"))

    def test_parse_list(self):
        self.assertListEqual(environment.parse_list("a, b, c"), ["a", "b", "c"])

    def test_parse_set(self):
        self.assertSetEqual(environment.parse_set("b, a, c"), {"a", "b", "c"})

    def test_env_wrapper(self):
        self.assertEqual(env.get("foo", "bar"), "bar")

        self.assertEqual(env.get("foo", "bar"), "bar")

        self.assertIsNone(env.get_bool("foobar"))

        self.assertFalse(env.get_bool("foobar", False))
        environ["foobar"] = "True"
        self.assertTrue(env.get_bool("foobar", False))
        environ["foobar"] = "Ture"
        self.assertIsNone(env.get_bool("foobar"))
        self.assertFalse(env.get_bool("foobar", False))

        environ["foobar"] = "123"
        self.assertEqual(env.get_int("foobar"), 123)

    def test_env_wrapper__can_parse_tuple(self):
        environ["foobar"] = "a, b, c"
        result = env.get_tuple("foobar")
        assert isinstance(result, tuple)
        self.assertTupleEqual(result, ("a", "b", "c"))

    def test_env_wrapper__can_parse_list(self):
        environ["foobar"] = "a, b, c"
        result = env.get_list("foobar")
        assert isinstance(result, list)
        self.assertListEqual(result, ["a", "b", "c"])

    def test_env_wrapper__can_parse_set(self):
        environ["foobar"] = "a, b, c"
        result = env.get_set("foobar")
        assert isinstance(result, set)
        self.assertSetEqual(result, {"a", "b", "c"})
        self.assertEqual(env.get("foobar"), "a, b, c")

    def test_env_wrapper__can_get_default_of_differing_type(self):
        self.assertIsNone(env.get_bool("foo", None))
        self.assertIsNone(env.get_bool("foo"))
