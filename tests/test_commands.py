from unittest import mock

import pytest
from django.core.management import call_command
from django.test import TestCase

from bananas.management.commands import show_urls

from .utils import drf_installed


class CommandTests(TestCase):
    @pytest.mark.skipif(
        not drf_installed(), reason="Django rest framework not installed"
    )
    def test_show_urls(self):
        urls = show_urls.collect_urls()

        admin_api_url_count = 45
        self.assertEqual(len(urls), admin_api_url_count)

        with mock.patch.object(show_urls.sys, "stdout", autospec=True) as stdout:  # type: ignore[attr-defined]
            show_urls.show_urls()

        self.assertEqual(stdout.write.call_count, admin_api_url_count)

        call_command("show_urls")
