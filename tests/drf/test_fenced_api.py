from functools import partial

from django.urls import reverse
from django.utils.http import http_date
from rest_framework import status
from rest_framework.test import APITestCase

from tests.models import Parent


class TestAllowIfUnmodifiedSince(APITestCase):
    url = partial(reverse, "if-unmodified-detail")

    def test_returns_bad_request_for_missing_header(self):
        item = Parent.objects.create()
        response = self.client.put(self.url(args=(item.pk,)), data={"name": "Great!"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"], "Header missing in request: If-Unmodified-Since"
        )

    def test_returns_bad_request_for_invalid_header(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_UNMODIFIED_SINCE="",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"],
            "Malformed header in request: If-Unmodified-Since",
        )

    def test_returns_precondition_failed_for_expired_token(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_UNMODIFIED_SINCE=http_date(item.date_modified.timestamp() - 1),
        )
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(
            response.json()["detail"],
            "The resource does not fulfill the given preconditions",
        )

    def test_allows_request_for_valid_token(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_UNMODIFIED_SINCE=http_date(item.date_modified.timestamp()),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"name": "Great!"})


class TestAllowIfMatch(APITestCase):
    url = partial(reverse, "if-match-detail")

    def test_returns_bad_request_for_missing_header(self):
        item = Parent.objects.create()
        response = self.client.put(self.url(args=(item.pk,)), data={"name": "Great!"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"], "Header missing in request: If-Match"
        )

    def test_returns_bad_request_for_invalid_header(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_MATCH="",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"], "Malformed header in request: If-Match"
        )

    def test_returns_precondition_failed_for_mismatching_token_set(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_MATCH='"abc123", "abc321", "abc123"',
        )
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(
            response.json()["detail"],
            "The resource does not fulfill the given preconditions",
        )

    def test_returns_precondition_failed_for_mismatching_single_token(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_MATCH='"abc123"',
        )
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(
            response.json()["detail"],
            "The resource does not fulfill the given preconditions",
        )

    def test_allows_request_for_single_valid_token(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_MATCH=item.version,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"name": "Great!"})

    def test_allows_request_for_set_with_matching_token(self):
        item = Parent.objects.create()
        response = self.client.put(
            self.url(args=(item.pk,)),
            data={"name": "Great!"},
            HTTP_IF_MATCH='"{}", "abc123"'.format(item.version),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"name": "Great!"})
