# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Prefix API: CRUD, hierarchy filters, utilization, available-subnets,
split (M3 draft contract; §12/§15/§17)."""

import pytest
from django.test import Client

from apps.prefixes.models import Prefix
from tests.factories import VRFFactory, make_role_user

pytestmark = pytest.mark.django_db

PREFIX_LIST = "/api/v1/prefixes/"


def _operator(client: Client) -> None:
    client.force_login(make_role_user("operator"))


def _create(client: Client, vrf_id: int, prefix: str, **extra: object) -> dict[str, object]:
    response = client.post(
        PREFIX_LIST,
        data={"vrf": vrf_id, "prefix": prefix, **extra},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    return response.json()


def test_create_strict_cidr_and_duplicate_codes(client: Client) -> None:
    vrf = VRFFactory()
    _operator(client)
    body = _create(client, vrf.id, "10.100.0.0/24")
    assert body["prefix"] == "10.100.0.0/24"
    # host bits → validation 400
    host_bits = client.post(
        PREFIX_LIST,
        data={"vrf": vrf.id, "prefix": "10.100.0.1/24"},
        content_type="application/json",
    )
    assert host_bits.status_code == 400
    # exact duplicate → 409 PREFIX_OVERLAP (stable code §17)
    dup = client.post(
        PREFIX_LIST,
        data={"vrf": vrf.id, "prefix": "10.100.0.0/24"},
        content_type="application/json",
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "PREFIX_OVERLAP"


def test_hierarchy_and_read_only_prefix(client: Client) -> None:
    vrf = VRFFactory()
    _operator(client)
    parent = _create(client, vrf.id, "172.20.0.0/24")
    child = _create(client, vrf.id, "172.20.0.128/25")
    # contains-filter finds parent and child from an inner address
    response = client.get(f"{PREFIX_LIST}?contains=172.20.0.130")
    found = {row["prefix"] for row in response.json()["results"]}
    assert found == {"172.20.0.0/24", "172.20.0.128/25"}
    # parent-filter: immediate children only
    children = client.get(f"{PREFIX_LIST}?parent={parent['id']}").json()["results"]
    assert [row["prefix"] for row in children] == ["172.20.0.128/25"]
    assert child["prefix"] == "172.20.0.128/25"
    # prefix is write-once
    patched = client.patch(
        f"{PREFIX_LIST}{child['id']}/",
        data={"prefix": "172.20.0.0/25", "status": "reserved"},
        content_type="application/json",
    )
    assert patched.status_code == 200
    assert patched.json()["prefix"] == "172.20.0.128/25"
    assert patched.json()["status"] == "reserved"


def test_invalid_contains_filter_is_400(client: Client) -> None:
    _operator(client)
    response = client.get(f"{PREFIX_LIST}?contains=not-an-ip")
    assert response.status_code == 400


def test_utilization_available_subnets_split(client: Client) -> None:
    vrf = VRFFactory()
    _operator(client)
    p = _create(client, vrf.id, "10.200.0.0/24")
    url = f"{PREFIX_LIST}{p['id']}/"

    used = client.post(f"{url}split/", data={"prefix_len": 26}, content_type="application/json")
    assert used.status_code == 201
    assert len(used.json()) == 4
    # split again → children exist; client-side invalid operation → 400
    again = client.post(f"{url}split/", data={"prefix_len": 26}, content_type="application/json")
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "PREFIX_SPLIT_INVALID"

    child = used.json()[0]
    client.post(f"{PREFIX_LIST}{child['id']}/allocate/", content_type="application/json")
    util = client.get(f"{url}utilization/").json()
    assert util["total"] == 254 and util["allocated"] == 1

    # free space: 4 children minus 1 address in the first → first /26 not free
    free = client.post(f"{url}available-subnets/", content_type="application/json")
    assert free.json()["available_subnets"] == []
    p2 = _create(client, vrf.id, "10.201.0.0/24")
    free2 = client.post(
        f"{PREFIX_LIST}{p2['id']}/available-subnets/",
        data={"masklen": 26},
        content_type="application/json",
    )
    assert len(free2.json()["available_subnets"]) == 4


def test_allocate_exhausted_and_invalid_masklen_codes(client: Client) -> None:
    vrf = VRFFactory()
    _operator(client)
    p = _create(client, vrf.id, "10.202.0.0/30")  # hosts: .1 .2
    url = f"{PREFIX_LIST}{p['id']}/"
    assert client.post(f"{url}allocate/", content_type="application/json").status_code == 201
    assert client.post(f"{url}allocate/", content_type="application/json").status_code == 201
    third = client.post(f"{url}allocate/", content_type="application/json")
    assert third.status_code == 409
    assert third.json()["error"]["code"] == "IP_ALLOCATION_EXHAUSTED"
    bad = client.post(
        f"{url}available-subnets/", data={"masklen": 8}, content_type="application/json"
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "PREFIX_INVALID"


def test_viewer_can_read_prefixes(client: Client) -> None:
    vrf = VRFFactory()
    p = Prefix.objects.create(vrf=vrf, prefix="10.203.0.0/24")
    client.force_login(make_role_user("viewer"))
    assert client.get(PREFIX_LIST).status_code == 200
    assert client.get(f"{PREFIX_LIST}{p.id}/utilization/").status_code == 200
    denied = client.post(
        PREFIX_LIST,
        data={"vrf": vrf.id, "prefix": "10.9.0.0/24"},
        content_type="application/json",
    )
    assert denied.status_code == 403
