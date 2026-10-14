# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
import json

import pytest
from django.test import Client

from tests.factories import make_role_user


@pytest.mark.django_db
def test_login_success_sets_session(client: Client) -> None:
    make_role_user("operator")  # placeholder to ensure groups exist
    from django.contrib.auth.models import User

    user = User.objects.get(username="user0")
    response = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"username": user.username, "password": "test-pass-123"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == user.username
    assert "operator" in body["roles"]


@pytest.mark.django_db
def test_login_wrong_password_401(client: Client) -> None:
    make_role_user("viewer")
    response = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"username": "user0", "password": "wrong"}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.django_db
def test_me_requires_auth(client: Client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_roles(client: Client) -> None:
    user = make_role_user("admin")
    client.force_login(user)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["roles"] == ["admin"]


@pytest.mark.django_db
def test_groups_bootstrapped() -> None:
    from django.contrib.auth.models import Group

    assert {"viewer", "operator", "admin"} <= set(Group.objects.values_list("name", flat=True))
