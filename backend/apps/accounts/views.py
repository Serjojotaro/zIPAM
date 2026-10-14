# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Browser auth endpoints (session cookies, ADR-0001). Not DRF: no model CRUD."""

import json

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.roles import user_roles


@require_GET
def auth_csrf(request: HttpRequest) -> JsonResponse:
    """Issue a CSRF token for the SPA (cookie stays HttpOnly, token in body).

    GET (safe method) so that the token bootstrap itself needs no CSRF."""
    return JsonResponse({"csrfToken": get_token(request)})


@require_POST
def auth_login(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body)
    except ValueError:
        return JsonResponse(
            {"error": {"code": "INVALID_JSON", "message": "Body must be JSON"}}, status=400
        )
    username = str(payload.get("username", ""))
    password = str(payload.get("password", ""))
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse(
            {"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid username or password."}},
            status=401,
        )
    login(request, user)
    return JsonResponse({"username": user.username, "roles": user_roles(user)})


@require_POST
def auth_logout(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({"status": "ok"})


def auth_me(request: HttpRequest) -> JsonResponse:
    user = request.user
    if not user.is_authenticated:
        return JsonResponse(
            {"error": {"code": "NOT_AUTHENTICATED", "message": "Authentication required."}},
            status=401,
        )
    return JsonResponse({"username": user.username, "roles": user_roles(user)})
