from django.test import TestCase
from django.urls import reverse
from django.utils.http import http_date
from rest_framework import status
from rest_framework.test import APITestCase
from tests.models import Parent


class TestFencedAPI(APITestCase):
    def test_returns_bad_request_for_missing_header(self):
        item = Parent.objects.create()
        url = reverse("fenced-detail", args=(item.pk,))
        response = self.client.put(url, data={"name": "Great!"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"], "Header missing in request: If-Unmodified-Since"
        )

    def test_returns_bad_request_for_invalid_header(self):
        item = Parent.objects.create()
        url = reverse("fenced-detail", args=(item.pk,))
        response = self.client.put(
            url,
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
        url = reverse("fenced-detail", args=(item.pk,))
        response = self.client.put(
            url,
            data={"name": "Great!"},
            HTTP_IF_UNMODIFIED_SINCE=http_date(item.date_modified.timestamp() - 1),
        )
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)
        self.assertEqual(
            response.json()["detail"], "The resource has been concurrently modified"
        )

    def test_allows_request_for_valid_token(self):
        item = Parent.objects.create()
        url = reverse("fenced-detail", args=(item.pk,))
        response = self.client.put(
            url,
            data={"name": "Great!"},
            HTTP_IF_UNMODIFIED_SINCE=http_date(item.date_modified.timestamp()),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"name": "Great!"})
