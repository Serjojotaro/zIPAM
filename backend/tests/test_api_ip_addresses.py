# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""IP address API: explicit assign, prefix allocate, release, filters
(M3; §13/§17)."""

import pytest
from django.test import Client

from apps.ip_addresses.models import IPAddress
from tests.factories import VRFFactory, make_role_user

pytestmark = pytest.mark.django_db

IP_LIST = "/api/v1/ip-addresses/"
PREFIX_LIST = "/api/v1/prefixes/"


def _operator(client: Client) -> None:
    client.force_login(make_role_user("operator"))


def _create_prefix(client: Client, vrf_id: int, prefix: str) -> int:
    response = client.post(
        PREFIX_LIST, data={"vrf": vrf_id, "prefix": prefix}, content_type="application/json"
    )
    assert response.status_code == 201, response.content
    return int(response.json()["id"])


def test_assign_explicit_address_and_errors(client: Client) -> None:
    vrf = VRFFactory()
    _operator(client)
    created = client.post(
        IP_LIST,
        data={"vrf": vrf.id, "address": "10.50.0.10", "status": "active"},
        content_type="application/json",
    )
    assert created.status_code == 201
    assert created.json()["address"] == "10.50.0.10"
    dup = client.post(
        IP_LIST, data={"vrf": vrf.id, "address": "10.50.0.10"}, content_type="application/json"
    )
    assert dup.status_code == 409, dup.content
    assert dup.json()["error"]["code"] == "IP_ALREADY_ALLOCATED"
    bad = client.post(
        IP_LIST, data={"vrf": vrf.id, "address": "10.50.0.0/24"}, content_type="application/json"
    )
    assert bad.status_code == 400


def test_allocate_from_prefix_and_release(client: Client) -> None:
    vrf = VRFFactory()
    _operator(client)
    prefix_id = _create_prefix(client, vrf.id, "10.51.0.0/30")
    first = client.post(
        f"{PREFIX_LIST}{prefix_id}/allocate/",
        data={"description": "host-a"},
        content_type="application/json",
    )
    assert first.status_code == 201
    assert first.json()["address"] == "10.51.0.1"
    assert first.json()["description"] == "host-a"
    released = client.delete(f"{IP_LIST}{first.json()['id']}/")
    assert released.status_code == 204
    assert not IPAddress.objects.filter(pk=first.json()["id"]).exists()
    second = client.post(f"{PREFIX_LIST}{prefix_id}/allocate/", content_type="application/json")
    assert second.json()["address"] == "10.51.0.1"  # smallest free again


def test_address_is_write_once(client: Client) -> None:
    vrf = VRFFactory()
    _operator(client)
    created = client.post(
        IP_LIST, data={"vrf": vrf.id, "address": "10.52.0.5"}, content_type="application/json"
    ).json()
    patched = client.patch(
        f"{IP_LIST}{created['id']}/",
        data={"address": "10.52.0.6", "status": "deprecated"},
        content_type="application/json",
    )
    assert patched.status_code == 200
    assert patched.json()["address"] == "10.52.0.5"
    assert patched.json()["status"] == "deprecated"


def test_filters_within_and_status(client: Client) -> None:
    vrf_a, vrf_b = VRFFactory(), VRFFactory()
    _operator(client)
    _create_prefix(client, vrf_a.id, "10.53.0.0/30")
    client.post(
        IP_LIST, data={"vrf": vrf_a.id, "address": "10.53.0.1"}, content_type="application/json"
    )
    client.post(
        IP_LIST,
        data={"vrf": vrf_a.id, "address": "10.53.0.2", "status": "reserved"},
        content_type="application/json",
    )
    client.post(
        IP_LIST, data={"vrf": vrf_b.id, "address": "10.53.9.3"}, content_type="application/json"
    )
    within = client.get(f"{IP_LIST}?within=10.53.0.0/30").json()
    assert {row["address"] for row in within["results"]} == {"10.53.0.1", "10.53.0.2"}
    by_vrf = client.get(f"{IP_LIST}?vrf={vrf_b.id}").json()
    assert [row["address"] for row in by_vrf["results"]] == ["10.53.9.3"]
    reserved = client.get(f"{IP_LIST}?status=reserved").json()
    assert [row["address"] for row in reserved["results"]] == ["10.53.0.2"]


def test_same_address_in_different_vrf(client: Client) -> None:
    a, b = VRFFactory(), VRFFactory()
    _operator(client)
    client.post(
        IP_LIST, data={"vrf": a.id, "address": "10.54.0.1"}, content_type="application/json"
    )
    same_in_other_vrf = client.post(
        IP_LIST, data={"vrf": b.id, "address": "10.54.0.1"}, content_type="application/json"
    )
    assert same_in_other_vrf.status_code == 201
