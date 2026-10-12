# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
import pytest
from django.test import Client


def test_health_ok(client: Client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_ready_ok(client: Client) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_api_requires_auth(client: Client) -> None:
    """Placeholder for §19: unauthenticated API access is denied once API exists."""
    response = client.get("/admin/login/")
    assert response.status_code == 200
