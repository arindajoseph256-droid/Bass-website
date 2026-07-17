from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


def custom_exception_handler(exc, context):
    """Custom exception handler for consistent API responses."""
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            "success": False,
            "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "status_code": response.status_code,
        }
        
        if hasattr(exc, "detail") and isinstance(exc.detail, dict):
            custom_response_data["errors"] = exc.detail
        elif hasattr(exc, "detail") and isinstance(exc.detail, list):
            custom_response_data["errors"] = exc.detail

        response.data = custom_response_data

    return response


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found."
    default_code = "not_found"


class PermissionDeniedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid input data."
    default_code = "validation_error"


class AuthenticationError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication credentials were not provided or are invalid."
    default_code = "authentication_error"


class ThrottledError(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Request was throttled."
    default_code = "throttled"


class InternalServerError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An unexpected error occurred."
    default_code = "internal_error"
