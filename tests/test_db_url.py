from urllib.parse import quote

from django.test import TestCase

from bananas import url

__test__ = {"Doctest": url}


class DBURLTest(TestCase):
    def test_sqlite_memory(self):
        conf = url.database_conf_from_url("sqlite://")

        self.assertDictEqual(
            conf,
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "",
                "USER": None,
                "HOST": None,
                "PORT": None,
                "PARAMS": {},
                "SCHEMA": None,
                "PASSWORD": None,
            },
        )

    def test_db_url(self):
        conf = url.database_conf_from_url(
            "pgsql://joar:hunter2@5monkeys.se:4242/tweets/tweetschema" "?hello=world"
        )

        self.assertDictEqual(
            conf,
            {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "HOST": "5monkeys.se",
                "NAME": "tweets",
                "PARAMS": {"hello": "world"},
                "PASSWORD": "hunter2",
                "PORT": 4242,
                "SCHEMA": "tweetschema",
                "USER": "joar",
            },
        )

    def test_alias(self):
        self.assertEqual(repr(url.Alias(target="x")), '<Alias to "x">')

    def test_register(self):
        url.register_engine("abc", "a.b.c")
        conf = url.database_conf_from_url("abc://5monkeys.se")
        self.maxDiff = None
        self.assertDictEqual(
            conf,
            {
                "ENGINE": "a.b.c",
                "HOST": "5monkeys.se",
                "NAME": "",
                "PARAMS": {},
                "PASSWORD": None,
                "PORT": None,
                "SCHEMA": None,
                "USER": None,
            },
        )

    def test_resolve(self):
        url.register_engine("abc", "a.b.c")
        self.assertRaises(KeyError, url.resolve, cursor={}, key="xyz")

    def test_get_engine(self):
        self.assertRaisesMessage(
            KeyError,
            "postgres has no sub-engines",
            url.get_engine,
            "postgres+psycopg2+postgis",
        )
        url.register_engine("a", ["b"])
        self.assertRaisesRegex(ValueError, r"^django-bananas\.url", url.get_engine, "a")
        url.register_engine("a", ["a", {"b": "c"}])
        self.assertEqual(url.get_engine("a+b"), "c")

    def test_parse(self):
        self.assertRaises(ValueError, url.parse_path, None)
        self.assertRaisesRegex(
            Exception, "^Your url is", url.parse_database_url, "sqlite://:memory:"
        )

    def test_db_url_with_slashes(self):
        name = quote("/var/db/tweets.sqlite", safe="")
        conf = url.database_conf_from_url("sqlite3:///{0}".format(name))

        self.assertDictEqual(
            conf,
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "/var/db/tweets.sqlite",
                "USER": None,
                "HOST": None,
                "PORT": None,
                "PARAMS": {},
                "SCHEMA": None,
                "PASSWORD": None,
            },
        )
