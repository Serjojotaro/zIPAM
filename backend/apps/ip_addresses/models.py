# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import ipaddress

from django.core.exceptions import ValidationError
from django.db import models

from apps.vrfs.models import VRF
from core.db.fields import InetField  # registers network lookups on import


class IPAddressStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    RESERVED = "reserved", "Reserved"
    DEPRECATED = "deprecated", "Deprecated"


class IPAddress(models.Model):
    """A single allocated/reserved address. Uniqueness is enforced by the
    database (UNIQUE per VRF), never by check-then-insert alone (§13)."""

    vrf = models.ForeignKey(VRF, on_delete=models.PROTECT, related_name="ip_addresses")
    address = InetField()
    status = models.CharField(
        max_length=20, choices=IPAddressStatus.choices, default=IPAddressStatus.ACTIVE
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vrf__name", "address"]
        constraints = [
            models.UniqueConstraint(fields=["vrf", "address"], name="uniq_ip_address_per_vrf"),
        ]

    def __str__(self) -> str:
        return f"{self.address} ({self.vrf.name})"

    def clean(self) -> None:
        super().clean()
        try:
            ipaddress.ip_address(str(self.address))
        except ValueError as exc:
            raise ValidationError({"address": "Enter a valid IPv4 or IPv6 address."}) from exc

    @property
    def ip(self) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        return ipaddress.ip_address(str(self.address))
