from django.core.management import call_command
from django.test import TestCase

from bananas.management.commands import show_urls


class CommandTests(TestCase):
    def test_show_urls(self):
        urls = show_urls.collect_urls()

        admin_api_url_count = 50
        self.assertEqual(len(urls), admin_api_url_count)

        class FakeSys:
            class stdout:
                lines = []

                @classmethod
                def write(cls, line):
                    cls.lines.append(line)

        show_urls.sys = FakeSys
        show_urls.show_urls()

        self.assertEqual(len(FakeSys.stdout.lines), admin_api_url_count)

        call_command("show_urls")
