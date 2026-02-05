import os
from pathlib import Path

from django.test import TestCase

from bananas import secrets


class EnvironmentVarGuard:
    def __init__(self):
        self._original = None

    def __enter__(self):
        self._original = os.environ.copy()
        return self

    def __exit__(self, exc_type, exc, tb):
        os.environ.clear()
        os.environ.update(self._original or {})

    def set(self, name, value):
        os.environ[str(name)] = str(value)

    def unset(self, name):
        os.environ.pop(name, None)


class SecretsTest(TestCase):
    def setUp(self):
        secrets_dir = str(Path(__file__).resolve().parent / "files")
        self.env = EnvironmentVarGuard()
        self.env.set(secrets.BANANAS_SECRETS_DIR_ENV_KEY, secrets_dir)

    def test_get_existing_secret(self):
        with self.env:
            secret = secrets.get_secret("hemlis")
        self.assertEqual(secret, "HEMLIS\n")

    def test_get_non_existing_secret_with_no_default(self):
        with self.env:
            secret = secrets.get_secret("doesnotexist")
        self.assertIsNone(secret)

    def test_get_non_existing_secret_with_default(self):
        default = "defaultvalue"
        with self.env:
            secret = secrets.get_secret("doesnotexist", default)
        self.assertEqual(secret, default)
