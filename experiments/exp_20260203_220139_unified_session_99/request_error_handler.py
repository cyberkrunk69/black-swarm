"""
request_error_handler.py

Provides comprehensive error handling utilities for request processing within the
application. This module defines custom exception types, a decorator to wrap
request handler functions, and helper functions to generate consistent error
responses.

Usage:

    from request_error_handler import handle_request_errors, RequestProcessingError

    @handle_request_errors
    def my_endpoint(request):
        # Your business logic here
        ...

The decorator catches expected and unexpected exceptions, logs them, and returns
a dictionary suitable for JSON serialization containing an HTTP status code,
an error code, and a human‑readable message.
"""

import json
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Tuple

# Configure a module‑level logger. In a real application this should be
# configured by the main entry point.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RequestProcessingError(Exception):
    """Base class for all request processing errors."""

    def __init__(self, message: str, *, error_code: str = "internal_error", status: int = 500):
        super().__init__(message)
        self.error_code = error_code
        self.status = status
        self.message = message


class BadRequestError(RequestProcessingError):
    """Raised when the client sends an invalid request."""

    def __init__(self, message: str = "Bad request", *, error_code: str = "bad_request"):
        super().__init__(message, error_code=error_code, status=400)


class UnauthorizedError(RequestProcessingError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized", *, error_code: str = "unauthorized"):
        super().__init__(message, error_code=error_code, status=401)


class NotFoundError(RequestProcessingError):
    """Raised when a requested resource cannot be found."""

    def __init__(self, message: str = "Not found", *, error_code: str = "not_found"):
        super().__init__(message, error_code=error_code, status=404)


class ConflictError(RequestProcessingError):
    """Raised when a request would cause a conflict (e.g., duplicate resource)."""

    def __init__(self, message: str = "Conflict", *, error_code: str = "conflict"):
        super().__init__(message, error_code=error_code, status=409)


def _build_error_response(exc: RequestProcessingError) -> Tuple[Dict[str, Any], int]:
    """
    Build a JSON‑serializable error response payload and the associated HTTP status.
    """
    response = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
        }
    }
    # Include debug trace only when explicitly enabled via environment variable.
    if logger.isEnabledFor(logging.DEBUG):
        response["error"]["trace"] = traceback.format_exc()
    return response, exc.status


def handle_request_errors(func: Callable) -> Callable:
    """
    Decorator that wraps a request handling function with comprehensive error handling.

    The wrapped function should accept a request object (or any arguments) and return
    a tuple ``(payload, status_code)`` where *payload* is JSON‑serializable.

    Any ``RequestProcessingError`` subclasses are caught and transformed into a
    standardized error payload. Unexpected exceptions are logged, wrapped in a
    generic ``RequestProcessingError`` (status 500), and returned as an internal
    server error response.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.debug("Entering request handler %s with args=%s kwargs=%s", func.__name__, args, kwargs)
            result = func(*args, **kwargs)

            # Allow handlers to return either (payload, status) or just payload.
            if isinstance(result, tuple) and len(result) == 2:
                payload, status = result
            else:
                payload, status = result, 200

            logger.debug("Handler %s succeeded with status=%s", func.__name__, status)
            return payload, status

        except RequestProcessingError as rp_err:
            logger.warning(
                "Handled request processing error in %s: %s (code=%s, status=%s)",
                func.__name__,
                rp_err.message,
                rp_err.error_code,
                rp_err.status,
            )
            return _build_error_response(rp_err)

        except Exception as exc:
            # Unexpected exception: log full stack trace and return generic 500.
            logger.error(
                "Unhandled exception in %s: %s",
                func.__name__,
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )
            generic_err = RequestProcessingError(
                "An unexpected error occurred. Please try again later.",
                error_code="internal_error",
                status=500,
            )
            return _build_error_response(generic_err)

    return wrapper


def json_response(payload: Any, status: int = 200) -> Tuple[str, int, Dict[str, str]]:
    """
    Helper to convert a payload to a JSON string and attach appropriate headers.
    Returns a tuple suitable for many WSGI/ASGI frameworks:
        (body_str, status_code, headers_dict)
    """
    try:
        body = json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        logger.error("Failed to serialize payload to JSON: %s", exc)
        # Fallback to a generic serialization error response.
        error_payload, error_status = _build_error_response(
            RequestProcessingError(
                "Failed to serialize response.",
                error_code="serialization_error",
                status=500,
            )
        )
        body = json.dumps(error_payload, ensure_ascii=False)
        status = error_status

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": str(len(body.encode("utf-8"))),
    }
    return body, status, headers


# Example usage (this block will not execute when imported):
if __name__ == "__main__":
    @handle_request_errors
    def demo_handler(request):
        if not request.get("valid"):
            raise BadRequestError("Missing 'valid' flag.")
        # Simulate processing
        return {"message": "Success"}, 200

    # Simulate a request
    fake_req = {"valid": False}
    response_body, response_status, response_headers = json_response(*demo_handler(fake_req))
    print("Status:", response_status)
    print("Headers:", response_headers)
    print("Body:", response_body)