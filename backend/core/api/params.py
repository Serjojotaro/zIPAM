# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Query-parameter helpers: invalid IP/CIDR filters are a 400 with a clear
message, never a ValueError surfacing from queryset evaluation (500)."""

from __future__ import annotations

import ipaddress

from rest_framework.exceptions import ValidationError


def parse_ip_or_cidr(value: str) -> str:
    try:
        if "/" in value:
            return str(ipaddress.ip_network(value, strict=False))
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise ValidationError({"detail": f"Invalid IP or CIDR value {value!r}: {exc}"}) from exc
