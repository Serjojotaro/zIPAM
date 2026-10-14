# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
import pytest
from django.test import Client

from apps.organizations.models import Organization
from tests.factories import OrganizationFactory, make_role_user

pytestmark = pytest.mark.django_db

ORG_LIST = "/api/v1/organizations/"


def test_anonymous_is_denied(client: Client) -> None:
    # DRF SessionAuthentication without WWW-Authenticate answers 403 to anonymous.
    assert client.get(ORG_LIST).status_code == 403


def test_viewer_can_read(client: Client) -> None:
    OrganizationFactory(name="ACME")
    client.force_login(make_role_user("viewer"))
    response = client.get(ORG_LIST)
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_viewer_cannot_write(client: Client) -> None:
    client.force_login(make_role_user("viewer"))
    response = client.post(ORG_LIST, data={"name": "Nope"}, content_type="application/json")
    assert response.status_code == 403
    assert not Organization.objects.filter(name="Nope").exists()


def test_operator_can_write(client: Client) -> None:
    client.force_login(make_role_user("operator"))
    response = client.post(ORG_LIST, data={"name": "Created"}, content_type="application/json")
    assert response.status_code == 201
    assert Organization.objects.filter(name="Created").exists()


def test_operator_patch_and_delete(client: Client) -> None:
    org = OrganizationFactory()
    client.force_login(make_role_user("operator"))
    url = f"{ORG_LIST}{org.id}/"
    patch_response = client.patch(url, data={"description": "upd"}, content_type="application/json")
    assert patch_response.status_code == 200
    assert client.delete(url).status_code == 204


def test_superuser_bypasses_roles(client: Client) -> None:
    from django.contrib.auth.models import User

    superuser = User.objects.create_superuser("root", "root@example.com", "super-pass-123")
    client.force_login(superuser)
    response = client.post(ORG_LIST, data={"name": "ByRoot"}, content_type="application/json")
    assert response.status_code == 201


def test_duplicate_org_name_rejected(client: Client) -> None:
    OrganizationFactory(name="Unique")
    client.force_login(make_role_user("operator"))
    response = client.post(ORG_LIST, data={"name": "Unique"}, content_type="application/json")
    assert response.status_code == 400
    assert "error" in response.json()
