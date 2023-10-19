from contextlib import contextmanager
from functools import wraps
from typing import ClassVar

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
    for model, model_admin in admin.site._registry.items():  # pragma: no branch
        if getattr(model, "View", object) is admin_view_cls:
            return model_admin


class SpecialModelAdmin(admin.ModelAdminView):
    pass


class AdminTest(TestCase):
    staff_user: ClassVar[User]

    @classmethod
    def setUpTestData(cls):
        call_command("syncpermissions")
        cls.staff_user = User.objects.create_user(
            username="user", password="test", is_staff=True
        )

    def setUp(self):
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

        ctx = admin.site.each_context(FakeRequest())  # type: ignore[arg-type]
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
        user = self.staff_user
        user.is_staff = False
        user.save(update_fields=["is_staff"])
        self.client.login(username=user.username, password="test")

        self.assert_unauthorized(self.custom_url)
        self.assert_unauthorized(self.detail_url)

    def test_admin_view_staff(self):
        staff_user = self.staff_user
        self.client.force_login(staff_user)

        # We need the correct permission
        self.assert_unauthorized(self.custom_url)
        self.assert_unauthorized(self.detail_url)

        perm = Permission.objects.filter(codename="can_access_simple").first()
        assert perm is not None
        staff_user.user_permissions.add(perm)

        expected_view_tools = {"Even more special action"}

        response = self.client.get(self.custom_url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context["context"], "custom")
        self.assertEqual(len(context["view_tools"]), 1)
        self.assertEqual(
            {t.text for t in context["view_tools"]},
            expected_view_tools,
        )

        response = self.client.get(self.detail_url)
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["context"], "get")
        self.assertEqual(len(context["view_tools"]), 1)
        self.assertEqual(
            {t.text for t in context["view_tools"]},
            expected_view_tools,
        )

    def test_admin_view_with_permission(self):
        staff_user = self.staff_user
        self.client.force_login(staff_user)

        self.assert_unauthorized(self.special_url)

        perm = Permission.objects.filter(codename="can_do_special_stuff").first()
        assert perm is not None
        staff_user.user_permissions.add(perm)
        expected_view_tools = {"Special Action", "Even more special action"}

        response = self.client.get(self.special_url)
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["context"], "special")
        self.assertEqual(len(context["view_tools"]), 2)
        self.assertEqual(
            {t.text for t in context["view_tools"]},
            expected_view_tools,
        )
        # No access to other views
        self.assert_unauthorized(self.custom_url)
        self.assert_unauthorized(self.detail_url)
