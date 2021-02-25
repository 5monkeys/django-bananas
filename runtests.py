#!/usr/bin/env python
import os
import sys
from typing import List, Optional

import django
from django.conf import settings
from django.test.utils import get_runner


def main(args: Optional[List[str]] = None) -> None:
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)

    test_targets = [args[0]] if args else ["tests"]
    failures = test_runner.run_tests(test_targets)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
