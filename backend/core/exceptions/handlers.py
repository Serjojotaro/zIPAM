# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""DRF exception handler producing the stable error envelope (§17)."""

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def _stable_code(exc: object, status: int) -> str:
    code = getattr(exc, "default_code", None)
    if isinstance(code, str):
        return code.upper()
    return f"HTTP_{status}"


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
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
