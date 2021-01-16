import datetime
from unittest import TestCase

from django.utils.http import http_date

from bananas.drf.utils import (
    InvalidHeader,
    MissingHeader,
    parse_header_datetime,
    parse_header_etags,
)

from .request import FakeRequest


class TestParseHeaderDatetime(TestCase):
    def test_raises_missing_header(self):
        request = FakeRequest.fake()
        with self.assertRaises(MissingHeader):
            parse_header_datetime(request, "missing")

    def test_raises_invalid_header(self):
        request = FakeRequest.fake(headers={"invalid": "not a date"})
        with self.assertRaises(InvalidHeader):
            parse_header_datetime(request, "invalid")

    def test_can_parse_datetime(self):
        dt = datetime.datetime(2021, 1, 14, 17, 30, 1, tzinfo=datetime.timezone.utc)
        request = FakeRequest.fake(headers={"valid": http_date(dt.timestamp())})
        self.assertEqual(dt, parse_header_datetime(request, "valid"))


class TestParseHeaderEtags(TestCase):
    def test_raises_missing_header(self):
        request = FakeRequest.fake()
        with self.assertRaises(MissingHeader):
            parse_header_etags(request, "missing")

    def test_raises_invalid_header(self):
        request = FakeRequest.fake(headers={"invalid": ""})
        with self.assertRaises(InvalidHeader):
            parse_header_etags(request, "invalid")

    def test_can_parse_single_etag(self):
        request = FakeRequest.fake(headers={"tag": '"value"'})
        self.assertSetEqual(parse_header_etags(request, "tag"), {"value"})

    def test_can_parse_many_tags(self):
        request = FakeRequest.fake(headers={"tag": '"a", "b"'})
        self.assertSetEqual(parse_header_etags(request, "tag"), {"a", "b"})
