# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Concurrency guarantees (§13): parallel allocate_ip into one prefix must
never double-allocate; UNIQUE(vrf, address) is the final backstop.

TransactionTestCase + real threads: each thread runs its own DB transaction,
SELECT ... FOR UPDATE serializes prefix allocation, IntegrityError guards
direct inserts.
"""

import threading

import pytest
from django.db import connection

from apps.ip_addresses.exceptions import IPAlreadyAllocatedError
from apps.ip_addresses.models import IPAddress
from apps.ip_addresses.services import allocate_ip, reserve_ip
from apps.prefixes.exceptions import PrefixOverlapError
from apps.prefixes.models import Prefix
from apps.prefixes.services import create_prefix
from tests.factories import VRFFactory


@pytest.mark.django_db(transaction=True)
def test_parallel_allocations_never_duplicate() -> None:
    vrf = VRFFactory()
    prefix = create_prefix(vrf, "10.99.0.0/29")  # 6 usable

    results: list[str] = []
    errors: list[BaseException] = []
    lock = threading.Lock()
    barrier = threading.Barrier(6)

    def worker() -> None:
        try:
            barrier.wait(timeout=10)
            ip = allocate_ip(prefix)
            with lock:
                results.append(str(ip.address))
        except BaseException as exc:  # noqa: BLE001 - re-raised in main thread
            with lock:
                errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"workers failed: {errors!r}"
    assert len(results) == 6
    assert len(set(results)) == 6, f"duplicate allocations: {results}"
    assert IPAddress.objects.filter(vrf=vrf).count() == 6


@pytest.mark.django_db(transaction=True)
def test_parallel_reserve_same_address_one_wins() -> None:
    vrf = VRFFactory()

    successes: list[str] = []
    failures: list[BaseException] = []
    lock = threading.Lock()
    barrier = threading.Barrier(4)

    def worker() -> None:
        try:
            barrier.wait(timeout=10)
            reserve_ip(vrf, "10.98.0.1")
            with lock:
                successes.append("ok")
        except BaseException as exc:  # noqa: BLE001
            with lock:
                failures.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert len(successes) == 1, f"expected exactly one winner: {successes}"
    assert len(failures) == 3
    assert all(isinstance(f, IPAlreadyAllocatedError) for f in failures)
    assert IPAddress.objects.filter(vrf=vrf, address="10.98.0.1").count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_duplicate_prefix_one_wins() -> None:
    """Concurrent identical creates: UNIQUE decides the winner; the losing
    thread gets a stable PrefixOverlapError, never a double row."""
    vrf = VRFFactory()

    created: list[str] = []
    failures: list[BaseException] = []
    lock = threading.Lock()
    barrier = threading.Barrier(4)

    def worker() -> None:
        try:
            barrier.wait(timeout=10)
            p = create_prefix(vrf, "10.97.0.0/24")
            with lock:
                created.append(str(p.prefix))
        except BaseException as exc:  # noqa: BLE001
            with lock:
                failures.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert len(created) == 1, f"duplicate rows leaked: {created} {failures}"
    assert all(isinstance(f, PrefixOverlapError) for f in failures)
    assert Prefix.objects.filter(vrf=vrf, prefix="10.97.0.0/24").count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_parent_and_child_both_ok() -> None:
    """Containment is hierarchy (§12), not conflict: parent and child created
    concurrently must both succeed."""
    vrf = VRFFactory()

    created: list[str] = []
    errors: list[BaseException] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def worker(cidr: str) -> None:
        try:
            barrier.wait(timeout=10)
            p = create_prefix(vrf, cidr)
            with lock:
                created.append(str(p.prefix))
        except BaseException as exc:  # noqa: BLE001
            with lock:
                errors.append(exc)
        finally:
            connection.close()

    threads = [
        threading.Thread(target=worker, args=(cidr,))
        for cidr in ("10.96.0.0/24", "10.96.0.128/25")
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"hierarchy race rejected: {errors}"
    assert sorted(created) == ["10.96.0.0/24", "10.96.0.128/25"]
