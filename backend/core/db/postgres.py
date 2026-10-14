# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""PostgreSQL inet/cidr operators as ORM lookups (ADR-0002).

Hierarchy and containment queries must run at the database level via the
network operators (>> << >>= <<= &&), not Python iteration over address
space (CLAUDE.md §12/§13). Registered onto core network fields in
core.db.fields.
"""

import ipaddress
from typing import Any

from django.db.models import Func, IntegerField
from django.db.models.lookups import PostgresOperatorLookup


class _NetLookup(PostgresOperatorLookup):
    """Operator lookups accept host addresses and prefixes on the RHS
    regardless of the declared field type (inet/cidr interop)."""

    def get_prep_lookup(self) -> Any:
        value = self.rhs
        if isinstance(value, str):
            text = value.strip()
            if "/" in text:
                return ipaddress.ip_network(text)
            try:
                return ipaddress.ip_address(text)
            except ValueError:
                pass  # leave for normal field prep / error reporting
        return value


class NetContains(_NetLookup):
    lookup_name = "net_contains"
    postgres_operator = ">>"


class NetContained(_NetLookup):
    lookup_name = "net_contained"
    postgres_operator = "<<"


class NetContainsOrEquals(_NetLookup):
    lookup_name = "net_contains_or_equals"
    postgres_operator = ">>="


class NetContainedOrEqual(_NetLookup):
    lookup_name = "net_contained_or_equal"
    postgres_operator = "<<="


class NetOverlap(_NetLookup):
    lookup_name = "net_overlap"
    postgres_operator = "&&"


class MaskLen(Func):
    """PostgreSQL masklen(inet|cidr) — prefix length at DB level."""

    function = "masklen"
    template = "%(function)s(%(expressions)s)"
    output_field = IntegerField()
