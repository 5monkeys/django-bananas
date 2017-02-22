import django
from django.core.management import call_command
from django.test import TestCase
from bananas.management.commands import show_urls


class CommandTests(TestCase):
    def test_show_urls(self):
        urls = show_urls.collect_urls()

        n_urls = 13 + int(django.VERSION >= (1, 9))
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
