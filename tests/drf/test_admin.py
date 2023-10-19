from contextlib import contextmanager
from functools import wraps
from typing import ClassVar

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from bananas import admin

rest_framework = pytest.importorskip("rest_framework")


class TestAPI(TestCase):
    user: ClassVar[User]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("syncpermissions")
        cls.user = User.objects.create_user(
            username="user", password="test", is_staff=True
        )

    def assertAuthorized(self):
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def assertNotAuthorized(self):
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_unautorized_schema(self):
        url = reverse("bananas:v1.0:schema", kwargs={"format": ".json"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("/bananas/login/", data["paths"])
        action = data["paths"]["/bananas/login/"]["post"]
        self.assertEqual(action["operationId"], "bananas.login:create")
        self.assertEqual(action["summary"], "Log in")
        self.assertNotIn("navigation", action["tags"])

    def test_autorized_schema(self):
        self.client.force_login(self.user)
        url = reverse("bananas:v1.0:schema", kwargs={"format": ".json"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.check_valid_schema(response.json())

    def check_valid_schema(self, data):
        self.assertNotIn("/bananas/login/", data["paths"])
        self.assertIn("/bananas/logout/", data["paths"])
        action = data["paths"]["/bananas/logout/"]["post"]
        self.assertEqual(action["operationId"], "bananas.logout:create")
        self.assertEqual(action["summary"], "Log out")
        self.assertNotIn("navigation", action["tags"])

        action = data["paths"]["/tests/ham/"]["get"]
        self.assertIn("crud", action["tags"])
        self.assertNotIn("navigation", action["tags"])

        action = data["paths"]["/bananas/me/"]["get"]
        self.assertNotIn("navigation", action["tags"])

        action = data["paths"]["/tests/foo/"]["get"]
        self.assertNotIn("crud", action["tags"])
        self.assertIn("navigation", action["tags"])

        bar_endpoint = data["paths"]["/tests/foo/bar/"]
        self.assertEqual(bar_endpoint["get"]["operationId"], "tests.foo:bar")
        self.assertNotIn("navigation", bar_endpoint["get"]["tags"])

        baz_endpoint = data["paths"]["/tests/foo/baz/"]
        self.assertEqual(baz_endpoint["get"]["operationId"], "tests.foo:baz.read")
        self.assertEqual(baz_endpoint["post"]["operationId"], "tests.foo:baz.create")
        self.assertIn("navigation", baz_endpoint["get"]["tags"])

    def test_login(self):
        user = self.user
        url = reverse("bananas:v1.0:bananas.login-list")

        # Fail
        response = self.client.post(
            url, data={"username": user.username, "password": "fail"}
        )
        self.assertEqual(response.status_code, 400)

        # Success
        response = self.client.post(
            url, data={"username": user.username, "password": "test"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], user.username)
        self.assertAuthorized()

    def test_logout(self):
        self.client.force_login(self.user)
        url = reverse("bananas:v1.0:bananas.logout-list")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertNotAuthorized()

    def test_me(self):
        user = self.user
        self.client.force_login(user)
        perm = Permission.objects.all().first()
        assert perm is not None
        group = Group.objects.create(name="spam")
        user.user_permissions.add(perm)
        user.groups.add(group)

        url = reverse("bananas:v1.0:bananas.me-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["username"], user.username)
        self.assertIn("spam", data["groups"])
        self.assertGreater(len(data["permissions"]), 0)

    def test_change_password(self):
        user = self.user
        self.client.force_login(user)
        url = reverse("bananas:v1.0:bananas.change_password-list")

        response = self.client.post(
            url,
            data={
                "old_password": "foo",
                "new_password1": "foo",
                "new_password2": "foo",
            },
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            url,
            data={
                "old_password": "test",
                "new_password1": "foo",
                "new_password2": "bar",
            },
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            url,
            data={
                "old_password": "test",
                "new_password1": "foobar123",
                "new_password2": "foobar123",
            },
        )
        self.assertEqual(response.status_code, 204)

        self.client.logout()
        self.client.login(username=user.username, password="test")
        self.assertNotAuthorized()

        self.client.login(username=user.username, password="foobar123")
        self.assertAuthorized()

    def test_tags_decorated_action(self):
        self.client.force_login(self.user)
        url = reverse("bananas:v1.0:tests.foo-bar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["bar"], True)
