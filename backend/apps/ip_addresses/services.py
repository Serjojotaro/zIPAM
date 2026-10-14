# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Transactional IP allocation (§13).

allocate_ip locks the prefix row (SELECT ... FOR UPDATE) so concurrent
allocations from the same prefix serialize, and the UNIQUE(vrf, address)
constraint is the final backstop — two requests can never hold one address.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterator

from django.db import IntegrityError, transaction

from apps.ip_addresses.exceptions import (
    IPAllocationExhaustedError,
    IPAlreadyAllocatedError,
    IPInvalidError,
)
from apps.ip_addresses.models import IPAddress, IPAddressStatus
from apps.prefixes.models import Prefix
from apps.vrfs.models import VRF
from core.db.postgres import NetContainedOrEqual  # noqa: F401  (registers lookups)

Address = ipaddress.IPv4Address | ipaddress.IPv6Address
Network = ipaddress.IPv4Network | ipaddress.IPv6Network


def _candidates(network: Network) -> Iterator[str]:
    """Candidate addresses in order, skipping network/broadcast for IPv4
    point-to-point semantics only where applicable (§11); IPv6 skips the
    subnet-router anycast address, links (/127, /128) keep all addresses."""
    if network.version == 6:
        if network.prefixlen >= 127:
            yield from (str(addr) for addr in network)
        else:
            yield from (str(addr) for addr in network.hosts())
        return
    if network.prefixlen <= 30:
        yield from (str(addr) for addr in network.hosts())
    else:
        yield from (str(addr) for addr in network)


def allocate_ip(
    prefix: Prefix,
    *,
    status: str = IPAddressStatus.ACTIVE,
    description: str = "",
    attempts: int = 3,
) -> IPAddress:
    for _ in range(attempts):
        try:
            with transaction.atomic():
                locked = Prefix.objects.select_for_update().get(pk=prefix.pk)
                taken = {
                    str(ipaddress.ip_address(raw))
                    for raw in IPAddress.objects.filter(
                        vrf_id=locked.vrf_id, address__net_contained_or_equal=locked.prefix
                    ).values_list("address", flat=True)
                }
                for candidate in _candidates(locked.network):
                    if str(ipaddress.ip_address(candidate)) in taken:
                        continue
                    ip = IPAddress(
                        vrf_id=locked.vrf_id, address=candidate, status=status,
                        description=description,
                    )
                    ip.save()
                    return ip
                raise IPAllocationExhaustedError(
                    f"No free addresses in {locked.prefix} ({locked.vrf.name})."
                )
        except IntegrityError:
            # A concurrent writer took this exact address (outside the prefix
            # lock). The transaction rolled back — recompute and retry.
            continue
    raise IPAlreadyAllocatedError(
        f"Allocation into {prefix.prefix} lost a concurrency race repeatedly."
    )


def reserve_ip(vrf: VRF, address: str, *, description: str = "") -> IPAddress:
    try:
        parsed = ipaddress.ip_address(str(address).strip())
    except ValueError as exc:
        raise IPInvalidError(f"Invalid IP address {address!r}.") from exc
    ip = IPAddress(
        vrf=vrf, address=str(parsed), status=IPAddressStatus.RESERVED, description=description
    )
    try:
        with transaction.atomic():
            ip.save()
    except IntegrityError as exc:
        raise IPAlreadyAllocatedError(
            f"Address {parsed} is already present in VRF {vrf.name}."
        ) from exc
    return ip


def release_ip(ip: IPAddress) -> bool:
    """Free an address (delete the allocation row; audit arrives in rc-02)."""
    _, deleted = ip.delete()
    return bool(deleted.get(IPAddress._meta.label))
