# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""IP allocation services: skip semantics, uniqueness, exhaustion
(CLAUDE.md §11/§13)."""

import pytest
from django.db import IntegrityError

from apps.ip_addresses.exceptions import (
    IPAllocationExhaustedError,
    IPAlreadyAllocatedError,
    IPInvalidError,
)
from apps.ip_addresses.models import IPAddress, IPAddressStatus
from apps.ip_addresses.services import allocate_ip, release_ip, reserve_ip
from apps.prefixes.services import create_prefix
from tests.factories import VRFFactory

pytestmark = pytest.mark.django_db


def test_allocate_skips_network_and_broadcast() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "10.0.0.0/29")
    first = allocate_ip(prefix)
    assert str(first.address) == "10.0.0.1"
    second = allocate_ip(prefix)
    assert str(second.address) == "10.0.0.2"
    # fill the rest; broadcast .7 must never be handed out
    for _ in range(3):
        allocate_ip(prefix)
    last = allocate_ip(prefix)
    assert str(last.address) == "10.0.0.6"
    with pytest.raises(IPAllocationExhaustedError):
        allocate_ip(prefix)
    assert not IPAddress.objects.filter(address="10.0.0.7").exists()
    assert not IPAddress.objects.filter(address="10.0.0.0").exists()


def test_allocate_skips_reserved() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "10.1.0.0/30")  # hosts: .1 .2
    reserve_ip(vrf, "10.1.0.1")
    ip = allocate_ip(prefix)
    assert str(ip.address) == "10.1.0.2"
    with pytest.raises(IPAllocationExhaustedError):
        allocate_ip(prefix)


def test_reserve_duplicate_and_invalid() -> None:
    vrf = VRFFactory()
    ip = reserve_ip(vrf, "10.2.0.5", description="gateway")
    assert ip.status == IPAddressStatus.RESERVED
    with pytest.raises(IPAlreadyAllocatedError):
        reserve_ip(vrf, "10.2.0.5")
    with pytest.raises(IPInvalidError):
        reserve_ip(vrf, "10.2.0.0/24")


def test_same_address_in_different_vrf() -> None:
    a, b = VRFFactory(), VRFFactory()
    reserve_ip(a, "10.3.0.1")
    ip = reserve_ip(b, "10.3.0.1")
    assert ip.vrf == b


def test_release_frees_address() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "10.4.0.0/30")
    ip = allocate_ip(prefix)
    assert release_ip(ip) is True
    again = allocate_ip(prefix)
    assert str(again.address) == "10.4.0.1"  # smallest free again


def test_ipv6_allocation_and_uniqueness() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "2001:db8:1::/64")
    first = allocate_ip(prefix)
    assert str(first.address) == "2001:db8:1::1"
    with pytest.raises(IntegrityError):
        dup = IPAddress(vrf=vrf, address="2001:db8:1::1")
        dup.save()
