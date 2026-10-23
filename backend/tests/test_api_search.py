# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Global search API (§14): IP/CIDR-aware matching plus name search."""

import pytest
from django.test import Client

from apps.ip_addresses.services import assign_ip
from apps.prefixes.services import create_prefix
from apps.vlans.models import VLAN
from tests.factories import (
    OrganizationFactory,
    PrefixFactory,
    TenantFactory,
    VRFFactory,
    make_role_user,
)

pytestmark = pytest.mark.django_db

SEARCH = "/api/v1/search"


def _operator(client: Client) -> None:
    client.force_login(make_role_user("operator"))


def test_search_requires_q_and_auth(client: Client) -> None:
    _operator(client)
    assert client.get(SEARCH).status_code == 400
    assert client.get(f"{SEARCH}?q=1").json()["error"]["code"] == "QUERY_TOO_SHORT"
    client.logout()
    assert client.get(f"{SEARCH}?q=core").status_code == 403


def test_search_by_ip_returns_address_and_containing_prefixes(client: Client) -> None:
    vrf = VRFFactory(name="core-peers")
    parent = create_prefix(vrf, "10.60.0.0/24")
    child = create_prefix(vrf, "10.60.0.128/25")
    assign_ip(vrf, "10.60.0.140", description="web-1")
    assert parent and child
    _operator(client)
    body = client.get(f"{SEARCH}?q=10.60.0.140").json()
    assert [row["address"] for row in body["results"]["ip_addresses"]] == ["10.60.0.140"]
    assert {row["prefix"] for row in body["results"]["prefixes"]} == {
        "10.60.0.0/24",
        "10.60.0.128/25",
    }


def test_search_by_cidr_finds_overlapping_prefixes(client: Client) -> None:
    vrf = VRFFactory()
    create_prefix(vrf, "10.61.0.0/24")
    create_prefix(vrf, "10.62.0.0/24")
    _operator(client)
    body = client.get(f"{SEARCH}?q=10.61.0.0/25").json()
    assert [row["prefix"] for row in body["results"]["prefixes"]] == ["10.61.0.0/24"]


def test_search_by_name_groups(client: Client) -> None:
    VRFFactory(name="dc-core")
    VLAN.objects.create(name="dc-core-lan", vid=77)
    OrganizationFactory(name="dc-core-ltd")
    TenantFactory(name="dc-core-tenant")
    _operator(client)
    body = client.get(f"{SEARCH}?q=dc-core").json()
    assert [row["name"] for row in body["results"]["vrfs"]] == ["dc-core"]
    assert [row["name"] for row in body["results"]["vlans"]] == ["dc-core-lan"]
    assert [row["name"] for row in body["results"]["organizations"]] == ["dc-core-ltd"]
    assert [row["name"] for row in body["results"]["tenants"]] == ["dc-core-tenant"]


def test_search_vlan_by_vid_and_prefix_text_fragment(client: Client) -> None:
    VLAN.objects.create(name="prod", vid=142)
    PrefixFactory(prefix="192.0.2.0/24")
    _operator(client)
    body = client.get(f"{SEARCH}?q=142").json()
    assert [row["vid"] for row in body["results"]["vlans"]] == [142]
    text = client.get(f"{SEARCH}?q=192.0.2").json()
    assert [row["prefix"] for row in text["results"]["prefixes"]] == ["192.0.2.0/24"]
