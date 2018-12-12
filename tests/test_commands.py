import django
from django.core.management import call_command
from django.test import TestCase

from bananas.management.commands import show_urls


class CommandTests(TestCase):
    def test_show_urls(self):
        urls = show_urls.collect_urls()

        if django.VERSION < (1, 9):
            n_urls = 23 + 8
        elif django.VERSION < (2, 0):
            n_urls = 25 + 8
        else:
            n_urls = 27 + 8

        self.assertEqual(len(urls), n_urls)

        class FakeSys:
            class stdout:
                lines = []

                @classmethod
                def write(cls, line):
                    cls.lines.append(line)

        show_urls.sys = FakeSys
        show_urls.show_urls()

        self.assertEqual(len(FakeSys.stdout.lines), n_urls)

        call_command('show_urls')
