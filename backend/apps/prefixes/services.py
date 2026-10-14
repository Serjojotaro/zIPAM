# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Prefix domain logic (§7): creation with overlap protection, hierarchy,
splitting, free-space computation, utilization. HTTP stays out of here."""

from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

from django.db import IntegrityError, transaction

from apps.prefixes.exceptions import PrefixInvalidError, PrefixOverlapError, PrefixSplitError
from apps.prefixes.models import Prefix, PrefixStatus
from apps.vrfs.models import VRF
from core.db.postgres import NetContained, NetContains, NetOverlap  # noqa: F401  (registrations)

if TYPE_CHECKING:
    from apps.organizations.models import Tenant
    from apps.sites.models import Site

Network = ipaddress.IPv4Network | ipaddress.IPv6Network


def _parse_strict(cidr: str) -> Network:
    value = str(cidr).strip()
    if "/" not in value:
        raise PrefixInvalidError(f"Prefix {cidr!r} must include a prefix length (CIDR).")
    try:
        return ipaddress.ip_network(value, strict=True)
    except ValueError as exc:
        raise PrefixInvalidError(f"Invalid prefix {cidr!r}: {exc}") from exc


def create_prefix(
    vrf: VRF,
    cidr: str,
    *,
    status: str = PrefixStatus.ACTIVE,
    tenant: Tenant | None = None,
    site: Site | None = None,
    description: str = "",
) -> Prefix:
    """Create a prefix inside a VRF.

    Containment is legal and forms the hierarchy (§12); the DB invariant is
    uniqueness of (VRF, prefix). The pre-check only improves the error
    message — UNIQUE is what guarantees it under concurrency.
    """
    network = _parse_strict(cidr)
    if Prefix.objects.filter(vrf=vrf, prefix=str(network)).exists():
        raise PrefixOverlapError(
            f"Prefix {network} already exists in VRF {vrf.name}.",
        )
    prefix = Prefix(
        vrf=vrf,
        prefix=str(network),
        status=status,
        tenant=tenant,
        site=site,
        description=description,
    )
    prefix.clean()
    try:
        with transaction.atomic():
            prefix.save()
    except IntegrityError as exc:
        raise PrefixOverlapError(
            f"Prefix {network} duplicates an existing prefix in VRF {vrf.name}."
        ) from exc
    return prefix


def split_prefix(prefix: Prefix, new_prefix_len: int) -> list[Prefix]:
    """Partition a prefix into equal children. Refuses when the prefix has
    children of its own or allocated addresses (§12 data integrity)."""
    network = prefix.network
    if not network.prefixlen < new_prefix_len <= network.max_prefixlen:
        raise PrefixSplitError(
            f"New prefix length /{new_prefix_len} must be longer than /{network.prefixlen}."
        )
    if prefix.children().exists():
        raise PrefixSplitError(f"Prefix {prefix.prefix} already has child prefixes.")
    from apps.ip_addresses.models import IPAddress

    if IPAddress.objects.filter(
        vrf_id=prefix.vrf_id, address__net_contained_or_equal=prefix.prefix
    ).exists():
        raise PrefixSplitError(f"Prefix {prefix.prefix} has allocated addresses.")

    children: list[Prefix] = []
    with transaction.atomic():
        for subnet in network.subnets(new_prefix=new_prefix_len):
            child = Prefix(
                vrf_id=prefix.vrf_id,
                prefix=str(subnet),
                status=prefix.status,
                tenant_id=prefix.tenant_id,
                site_id=prefix.site_id,
            )
            child.clean()
            child.save()
            children.append(child)
    return children


def available_subnets(prefix: Prefix, masklen: int | None = None) -> list[str]:
    """Free space of a prefix as a list of CIDRs, computed from the bounded
    set of child prefixes fetched via DB containment (not address scanning)."""
    network = prefix.network
    if masklen is not None and not (network.prefixlen < masklen <= network.max_prefixlen):
        raise PrefixInvalidError(f"masklen {masklen} must be longer than /{network.prefixlen}.")
    children = [
        ipaddress.ip_network(str(cidr))
        for cidr in prefix.children().values_list("prefix", flat=True)
    ]
    if masklen is None:
        return [str(net) for net in _subtract(network, children)]
    return [
        str(subnet)
        for subnet in network.subnets(new_prefix=masklen)
        if not any(_overlaps(subnet, child) for child in children)
    ]


def _overlaps(a: Network, b: Network) -> bool:
    return a.overlaps(b)


def _contained(inner: Network, outer: Network) -> bool:
    # ipaddress compares only same-version networks; a prefix tree never
    # mixes families, but narrow explicitly so the type checker agrees.
    if isinstance(inner, ipaddress.IPv4Network) and isinstance(outer, ipaddress.IPv4Network):
        return inner.subnet_of(outer)
    if isinstance(inner, ipaddress.IPv6Network) and isinstance(outer, ipaddress.IPv6Network):
        return inner.subnet_of(outer)
    return False


def _subtract(network: Network, used: list[Network]) -> list[Network]:
    """Collapse free space of `network` minus CIDR list `used` (recursive
    half-splitting; cost is O(len(used) * prefixbits), not O(2^bits))."""
    used = sorted(used, key=lambda n: (int(n.network_address), n.prefixlen))
    result: list[Network] = []

    def walk(current: Network) -> None:
        for used_net in used:
            if not _overlaps(current, used_net):
                continue
            if _contained(current, used_net):
                return  # fully covered by an allocated block
            for half in current.subnets():
                walk(half)
            return
        result.append(current)

    walk(network)
    return result


def _usable_address_count(network: Network) -> int:
    if network.version == 4 and network.prefixlen <= 30:
        return network.num_addresses - 2  # network + broadcast
    return network.num_addresses


def calculate_utilization(prefix: Prefix) -> dict[str, int | float]:
    """Allocated/reserved addresses contained in the prefix vs usable space (§23)."""
    from apps.ip_addresses.models import IPAddress

    network = prefix.network
    total = _usable_address_count(network)
    allocated = IPAddress.objects.filter(
        vrf_id=prefix.vrf_id, address__net_contained_or_equal=prefix.prefix
    ).count()
    percent = round(allocated / total * 100, 2) if total else 0.0
    return {
        "total": total,
        "allocated": allocated,
        "available": max(total - allocated, 0),
        "utilization_percent": percent,
    }
