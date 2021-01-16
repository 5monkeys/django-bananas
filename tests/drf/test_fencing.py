import datetime
import operator
from unittest import TestCase

from django.utils.http import http_date
from rest_framework.exceptions import ValidationError

from bananas.drf.errors import BadRequest
from bananas.drf.fencing import (
    Fence,
    header_date_parser,
    header_etag_parser,
    parse_date_modified,
)
from bananas.models import TimeStampedModel

from .request import FakeRequest


class TestFence(TestCase):
    def test_check_propagates_error_from_get_token(self):
        error = RuntimeError()

        def get_token(_request):
            raise error

        def get_version(_instance):
            return "a"

        fence = Fence(get_token=get_token, compare=operator.eq, get_version=get_version)

        with self.assertRaises(RuntimeError) as exc_info:
            fence.check(FakeRequest.fake(), "a")

        self.assertIs(exc_info.exception, error)

    def test_check_propagates_error_from_get_version(self):
        error = RuntimeError()

        def get_token(_request):
            return "a"

        def get_version(_instance):
            raise error

        fence = Fence(get_token=get_token, compare=operator.eq, get_version=get_version)

        with self.assertRaises(RuntimeError) as exc_info:
            fence.check(FakeRequest.fake(), "a")

        self.assertIs(exc_info.exception, error)

    def test_check_returns_true_for_valid_token(self):
        def get_token(_request):
            return "a"

        def get_version(_instance):
            return "a"

        fence = Fence(get_token=get_token, compare=operator.eq, get_version=get_version)

        self.assertIs(fence.check(FakeRequest.fake(), "a"), True)

    def test_check_returns_false_for_invalid_token(self):
        def get_token(_request):
            return "a"

        def get_version(_instance):
            return "b"

        fence = Fence(get_token=get_token, compare=operator.eq, get_version=get_version)

        self.assertIs(fence.check(FakeRequest.fake(), "a"), False)


class TestHeaderDateParser(TestCase):
    def test_raises_bad_request_for_header_error(self):
        get_header = header_date_parser("header")
        with self.assertRaises(BadRequest) as exc_info:
            get_header(FakeRequest.fake())
        self.assertEqual(exc_info.exception.detail.code, "missing_header")

    def test_can_get_parsed_header_datetime(self):
        dt = datetime.datetime(2021, 1, 14, 17, 30, 1, tzinfo=datetime.timezone.utc)
        request = FakeRequest.fake(headers={"header": http_date(dt.timestamp())})
        parsed = header_date_parser("header")(request)
        self.assertEqual(parsed, dt)


class TestDateModifiedGetter(TestCase):
    def test_replaces_microsecond(self):
        class A(TimeStampedModel):
            date_modified = datetime.datetime(
                2021, 1, 14, 17, 30, 1, 1, tzinfo=datetime.timezone.utc
            )

        self.assertEqual(
            parse_date_modified(A()),
            datetime.datetime(2021, 1, 14, 17, 30, 1, tzinfo=datetime.timezone.utc),
        )

    def test_can_get_none(self):
        class A(TimeStampedModel):
            date_modified = None

        self.assertIsNone(parse_date_modified(A()))


class TestHeaderEtagParser(TestCase):
    def test_can_parse_multiple_etags(self):
        request = FakeRequest.fake(headers={"If-Match": '"a", "b"'})
        self.assertSetEqual(header_etag_parser("If-Match")(request), {"a", "b"})

    def test_can_parse_single_etag(self):
        request = FakeRequest.fake(headers={"If-Match": '"a"'})
        self.assertSetEqual(header_etag_parser("If-Match")(request), {"a"})

    def test_raises_bad_request_error_for_missing_header(self):
        request = FakeRequest.fake()
        parser = header_etag_parser("If-Match")
        with self.assertRaises(BadRequest) as exc_info:
            parser(request)
        self.assertEqual(exc_info.exception.detail.code, "missing_header")

    def test_raises_bad_request_for_invalid_header(self):
        request = FakeRequest.fake(headers={"If-Match": ""})
        parser = header_etag_parser("If-Match")
        with self.assertRaises(BadRequest) as exc_info:
            parser(request)
        self.assertEqual(exc_info.exception.detail.code, "invalid_header")
