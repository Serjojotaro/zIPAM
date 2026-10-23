# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""VRF/VLAN CRUD API: roles, validation, protected delete (§19, §67)."""

import pytest
from django.test import Client

from apps.vlans.models import VLAN
from apps.vrfs.models import VRF
from tests.factories import PrefixFactory, VRFFactory, make_role_user

pytestmark = pytest.mark.django_db

VRF_LIST = "/api/v1/vrfs/"
VLAN_LIST = "/api/v1/vlans/"


def _operator(client: Client) -> None:
    client.force_login(make_role_user("operator"))


def test_viewer_reads_vrfs_but_cannot_write(client: Client) -> None:
    VRFFactory(name="prod")
    client.force_login(make_role_user("viewer"))
    response = client.get(VRF_LIST)
    assert response.status_code == 200
    denied = client.post(VRF_LIST, data={"name": "x"}, content_type="application/json")
    assert denied.status_code == 403


def test_operator_creates_vrf_and_updates(client: Client) -> None:
    _operator(client)
    created = client.post(
        VRF_LIST, data={"name": "dc1", "rd": "65000:100"}, content_type="application/json"
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "dc1" and body["rd"] == "65000:100"
    patched = client.patch(
        f"{VRF_LIST}{body['id']}/", data={"description": "up"}, content_type="application/json"
    )
    assert patched.status_code == 200
    assert patched.json()["description"] == "up"


def test_vrf_duplicate_name_rejected(client: Client) -> None:
    VRFFactory(name="dup")
    _operator(client)
    response = client.post(VRF_LIST, data={"name": "dup"}, content_type="application/json")
    assert response.status_code == 400


def test_vrf_with_prefixes_protected(client: Client) -> None:
    vrf = VRFFactory()
    PrefixFactory(vrf=vrf)
    _operator(client)
    response = client.delete(f"{VRF_LIST}{vrf.id}/")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REFERENCE_PROTECTED"
    assert VRF.objects.filter(pk=vrf.pk).exists()


def test_vlan_crud_and_vid_bounds(client: Client) -> None:
    _operator(client)
    created = client.post(
        VLAN_LIST, data={"name": "core", "vid": 10}, content_type="application/json"
    )
    assert created.status_code == 201
    for vid in (0, 4095):
        bad = client.post(
            VLAN_LIST, data={"name": "core", "vid": vid}, content_type="application/json"
        )
        assert bad.status_code == 400


def test_vlan_duplicate_vid_name_rejected(client: Client) -> None:
    VLAN.objects.create(name="core", vid=100)
    _operator(client)
    response = client.post(
        VLAN_LIST, data={"name": "core", "vid": 100}, content_type="application/json"
    )
    assert response.status_code == 400
    # same vid, other name is legal
    assert (
        client.post(
            VLAN_LIST, data={"name": "office", "vid": 100}, content_type="application/json"
        ).status_code
        == 201
    )
