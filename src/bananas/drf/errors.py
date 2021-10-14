from rest_framework import status
from rest_framework.exceptions import APIException


class PreconditionFailed(APIException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = "An HTTP precondition failed"
    default_code = "precondition_failed"


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation failed"
    default_code = "bad_request"
