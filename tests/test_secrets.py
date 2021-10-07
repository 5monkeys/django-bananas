import os

try:
    from test.support.os_helper import EnvironmentVarGuard  # type: ignore[import]
except ImportError:
    # Compatibility for Python <=3.9
    from test.support import EnvironmentVarGuard

from django.test import TestCase

from bananas import secrets


class SecretsTest(TestCase):
    def setUp(self):
        secrets_dir = os.path.join(os.path.dirname(__file__), "files")
        self.env = EnvironmentVarGuard()
        self.env.set(secrets.BANANAS_SECRETS_DIR_ENV_KEY, secrets_dir)

    def test_get_existing_secret(self):
        with self.env:
            secret = secrets.get_secret("hemlis")
        self.assertEqual(secret, "HEMLIS")

    def test_get_non_existing_secret_with_no_default(self):
        with self.env:
            secret = secrets.get_secret("doesnotexist")
        self.assertIsNone(secret)

    def test_get_non_existing_secret_with_default(self):
        default = "defaultvalue"
        with self.env:
            secret = secrets.get_secret("doesnotexist", default)
        self.assertEqual(secret, default)
