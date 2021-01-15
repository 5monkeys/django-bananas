import datetime
from unittest import TestCase

from django.utils.http import http_date

from bananas.drf.utils import parse_header_datetime

from .request import FakeRequest


class TestParseHeaderDatetime(TestCase):
    def test_raises_value_error_for_missing_header(self):
        request = FakeRequest.fake()
        with self.assertRaisesRegex(
            ValueError, r"^Header missing in request: missing_header$"
        ):
            parse_header_datetime(request, "missing_header")

    def test_raises_value_error_for_invalid_header_value(self):
        request = FakeRequest.fake(headers={"invalid": "not a date"})
        with self.assertRaisesRegex(
            ValueError, r"^Malformed header in request: invalid$"
        ):
            parse_header_datetime(request, "invalid")

    def test_can_parse_datetime(self):
        dt = datetime.datetime(2021, 1, 14, 17, 30, 1, tzinfo=datetime.timezone.utc)
        request = FakeRequest.fake(headers={"valid": http_date(dt.timestamp())})
        self.assertEqual(dt, parse_header_datetime(request, "valid"))
