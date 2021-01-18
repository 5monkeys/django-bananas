from contextlib import contextmanager
from functools import wraps

from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from bananas import admin


@contextmanager
def override_admin_registry():
    initial_registry = admin.site._registry.copy()
    try:
        yield
    finally:
        admin.site._registry = initial_registry


def reset_admin_registry(method):
    @wraps(method)
    def wrapped(*args, **kwargs):
        with override_admin_registry():
            return method(*args, **kwargs)

    return wrapped


def get_model_admin_from_registry(admin_view_cls):
    for model, model_admin in admin.site._registry.items():
        if getattr(model, "View", object) is admin_view_cls:
            return model_admin


class SpecialModelAdmin(admin.ModelAdminView):
    pass


class AdminBaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("syncpermissions")

    def create_user(self, staff=True):
        user = User.objects.create_user(username="user", password="test")
        if staff:
            user.is_staff = True
            user.save()
        return user

    def login_user(self, staff=True):
        user = self.create_user(staff=staff)
        self.client.login(username=user.username, password="test")
        return user

    def assertAuthorized(self):
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def assertNotAuthorized(self):
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login


class AdminTest(AdminBaseTest):
    def setUp(self):
        super().setUp()
        self.detail_url = reverse("admin:tests_simple")
        self.custom_url = reverse("admin:tests_simple_custom")
        self.special_url = reverse("admin:tests_simple_special")

    @reset_admin_registry
    def test_admin(self):
        @admin.register
        class AnAdminView(admin.AdminView):
            __module__ = "tests.admin"

        class FakeRequest:
            META = {"SCRIPT_NAME": ""}
            user = AnonymousUser()

        ctx = admin.site.each_context(FakeRequest())
        self.assertTrue("settings" in ctx)
        self.assertIsInstance(admin.site.urls, tuple)

    @reset_admin_registry
    def test_register_without_args(self):

        # As decorator without arguments
        @admin.register
        class MyAdminViewRegisteredWithoutArgs(admin.AdminView):
            __module__ = "tests.admin"

        model_admin = get_model_admin_from_registry(MyAdminViewRegisteredWithoutArgs)
        self.assertIsNotNone(model_admin)
        self.assertIsInstance(model_admin, admin.ModelAdminView)

    @reset_admin_registry
    def test_register_with_args(self):

        # As decorator with arguments
        @admin.register(admin_class=SpecialModelAdmin)
        class MyAdminViewRegisteredWithArgs(admin.AdminView):
            __module__ = "tests.admin"

        model_admin = get_model_admin_from_registry(MyAdminViewRegisteredWithArgs)
        self.assertIsNotNone(model_admin)
        self.assertIsInstance(model_admin, SpecialModelAdmin)

    @reset_admin_registry
    def test_register_normally(self):

        # Just registered
        class MyAdminViewRegisteredNormally(admin.AdminView):
            __module__ = "tests.admin"

        admin.register(MyAdminViewRegisteredNormally, admin_class=SpecialModelAdmin)
        model_admin = get_model_admin_from_registry(MyAdminViewRegisteredNormally)
        self.assertIsNotNone(model_admin)
        self.assertIsInstance(model_admin, SpecialModelAdmin)

    @reset_admin_registry
    def test_register_app_nested_in_package(self):
        @admin.register
        class MyAdminViewRegisteredInNestedApp(admin.AdminView):
            __module__ = "somepackage.tests.admin"

        model_admin = get_model_admin_from_registry(MyAdminViewRegisteredInNestedApp)
        self.assertIsNotNone(model_admin)
        self.assertIsInstance(model_admin, admin.ModelAdminView)

    def assert_unauthorized(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            "{}?next={}".format(reverse("admin:login"), url),
            fetch_redirect_response=False,
        )

    def test_admin_view_non_staff(self):
        normal_user = self.login_user(staff=False)
        self.client.login(username=normal_user.username, password="test")

        self.assert_unauthorized(self.custom_url)
        self.assert_unauthorized(self.detail_url)

    def test_admin_view_staff(self):
        staff_user = self.login_user()

        # We need the correct permission
        self.assert_unauthorized(self.custom_url)
        self.assert_unauthorized(self.detail_url)

        perm = Permission.objects.filter(codename="can_access_simple").first()
        self.assertIsNotNone(perm)
        staff_user.user_permissions.add(perm)

        expected_view_tools = {"Even more special action"}

        response = self.client.get(self.custom_url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context["context"], "custom")
        self.assertEqual(len(context["view_tools"]), 1)
        self.assertEqual(
            set(t.text for t in context["view_tools"]), expected_view_tools
        )

        response = self.client.get(self.detail_url)
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["context"], "get")
        self.assertEqual(len(context["view_tools"]), 1)
        self.assertEqual(
            set(t.text for t in context["view_tools"]), expected_view_tools
        )

    def test_admin_view_with_permission(self):
        staff_user = self.login_user()

        self.assert_unauthorized(self.special_url)

        perm = Permission.objects.filter(codename="can_do_special_stuff").first()
        self.assertIsNotNone(perm)
        staff_user.user_permissions.add(perm)
        expected_view_tools = {"Special Action", "Even more special action"}

        response = self.client.get(self.special_url)
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["context"], "special")
        self.assertEqual(len(context["view_tools"]), 2)
        self.assertEqual(
            set(t.text for t in context["view_tools"]), expected_view_tools
        )
        # No access to other views
        self.assert_unauthorized(self.custom_url)
        self.assert_unauthorized(self.detail_url)


class APITest(AdminBaseTest):
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
        self.login_user()
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
        user = self.create_user()
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
        self.login_user()
        url = reverse("bananas:v1.0:bananas.logout-list")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertNotAuthorized()

    def test_me(self):
        user = self.login_user()
        perm = Permission.objects.all().first()
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
        user = self.login_user()
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
        self.login_user()
        url = reverse("bananas:v1.0:tests.foo-bar")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["bar"], True)
