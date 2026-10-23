# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""DRF exception handler producing the stable error envelope (§17)."""

from typing import Any

from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.exceptions.domain import DomainError

# Stable domain code → HTTP status (§17); unknown domain codes default to 409.
_DOMAIN_STATUS = {
    "PREFIX_INVALID": 400,
    "PREFIX_SPLIT_INVALID": 400,
    "IP_INVALID": 400,
}


def _stable_code(exc: object, status: int) -> str:
    code = getattr(exc, "default_code", None)
    if isinstance(code, str):
        return code.upper()
    return f"HTTP_{status}"


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DomainError):
        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
            status=_DOMAIN_STATUS.get(exc.code, 409),
        )
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "error": {
                    "code": "REFERENCE_PROTECTED",
                    "message": "Object is referenced by other objects and cannot be deleted.",
                    "details": {
                        "protected_objects": [str(obj) for obj in list(exc.protected_objects)[:10]],
                    },
                }
            },
            status=409,
        )
    response = exception_handler(exc, context)
    if response is None:
        return None
    status = response.status_code
    detail = response.data
    message = str(detail.get("detail", detail)) if isinstance(detail, dict) else str(detail)
    response.data = {
        "error": {
            "code": _stable_code(exc, status),
            "message": message,
            "details": detail if isinstance(detail, (dict, list)) else {},
        }
    }
    return response
