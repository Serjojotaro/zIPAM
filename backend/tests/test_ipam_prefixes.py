# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Prefix model/services: overlap protection, hierarchy, split, free space,
utilization (CLAUDE.md §12, §23; ADR-0002)."""


import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.ip_addresses.services import allocate_ip, reserve_ip
from apps.prefixes.exceptions import PrefixInvalidError, PrefixOverlapError, PrefixSplitError
from apps.prefixes.models import Prefix
from apps.prefixes.services import (
    available_subnets,
    calculate_utilization,
    create_prefix,
    split_prefix,
)
from tests.factories import VRFFactory

pytestmark = pytest.mark.django_db


def test_create_and_strict_cidr_validation() -> None:
    vrf = VRFFactory()
    p = create_prefix(vrf, "192.168.10.0/24")
    assert str(p.prefix) == "192.168.10.0/24"
    with pytest.raises(PrefixInvalidError):
        create_prefix(vrf, "192.168.10.1/24")  # host bits set
    with pytest.raises(PrefixInvalidError):
        create_prefix(vrf, "192.168.10.0")  # no prefix length


def test_hierarchy_containment_is_legal_duplicates_rejected() -> None:
    """Strict CIDRs never partially overlap — containment IS the hierarchy (§12).
    Only exact (VRF, prefix) duplicates are rejected; the same prefix in a
    different VRF is a distinct routing object."""
    vrf_a, vrf_b = VRFFactory(), VRFFactory()
    parent = create_prefix(vrf_a, "10.0.0.0/24")
    child = create_prefix(vrf_a, "10.0.0.128/25")
    # creating the parent of an existing prefix is legal (re-parenting)
    grandparent = create_prefix(vrf_a, "10.0.0.0/23")
    assert child in parent.children()
    assert parent in grandparent.children()
    with pytest.raises(PrefixOverlapError):
        create_prefix(vrf_a, "10.0.0.0/24")  # exact duplicate
    other = create_prefix(vrf_b, "10.0.0.128/25")
    assert other.vrf == vrf_b


def test_duplicate_prefix_rejected_at_db_level() -> None:
    """UNIQUE(vrf, prefix) is the authoritative guard, not check-then-insert."""
    vrf = VRFFactory()
    Prefix.objects.create(vrf=vrf, prefix="172.16.5.0/24")
    dup = Prefix(vrf=vrf, prefix="172.16.5.0/24")
    with pytest.raises(IntegrityError), transaction.atomic():
        dup.save()


def test_hierarchy_via_db_containment() -> None:
    vrf = VRFFactory()
    parent = create_prefix(vrf, "10.10.0.0/16")
    child1 = create_prefix(vrf, "10.10.1.0/24")
    grandchild = create_prefix(vrf, "10.10.1.128/25")
    child2 = create_prefix(vrf, "10.10.2.0/24")

    assert child1.get_parent() == parent
    assert grandchild.get_parent() == child1
    assert parent.get_parent() is None
    assert set(parent.immediate_children()) == {child1, child2}
    assert set(parent.children()) == {child1, child2, grandchild}
    assert grandchild in parent.children()
    assert not grandchild.ancestor_of(parent)
    assert parent.ancestor_of(grandchild)


def test_split_and_validation() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "10.20.0.0/24")
    children = split_prefix(prefix, 26)
    assert [str(c.prefix) for c in children] == [
        "10.20.0.0/26",
        "10.20.0.64/26",
        "10.20.0.128/26",
        "10.20.0.192/26",
    ]
    with pytest.raises(PrefixSplitError):
        split_prefix(prefix, 26)  # already has children
    with pytest.raises(PrefixSplitError):
        split_prefix(children[0], 24)  # shorter than parent

    occupied = create_prefix(vrf, "10.30.0.0/24")
    reserve_ip(vrf, "10.30.0.10")
    with pytest.raises(PrefixSplitError):
        split_prefix(occupied, 25)  # allocated addresses


def test_available_subnets() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "10.40.0.0/24")
    create_prefix(vrf, "10.40.0.64/26")
    create_prefix(vrf, "10.40.0.128/25")
    # children cover 64-255; free space is only 0-63
    assert available_subnets(prefix) == ["10.40.0.0/26"]
    assert available_subnets(prefix, masklen=27) == ["10.40.0.0/27", "10.40.0.32/27"]


def test_utilization() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "10.50.0.0/29")  # 6 usable (hosts)
    allocate_ip(prefix)  # .1
    allocate_ip(prefix)  # .2
    reserve_ip(vrf, "10.50.0.3")
    util = calculate_utilization(prefix)
    assert util["total"] == 6
    assert util["allocated"] == 3
    assert util["available"] == 3
    assert util["utilization_percent"] == 50.0


def test_vlan_vid_bounds() -> None:
    from apps.vlans.models import VLAN

    vlan = VLAN(name="core", vid=100)
    vlan.full_clean()
    bad = VLAN(name="bad", vid=4095)
    with pytest.raises(ValidationError):
        bad.full_clean()
