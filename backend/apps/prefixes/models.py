# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

from django.contrib.postgres.indexes import GistIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet

from apps.vrfs.models import VRF
from core.db.fields import CidrField  # registers network lookups on import
from core.db.postgres import MaskLen

if TYPE_CHECKING:
    from apps.ip_addresses.models import IPAddress  # noqa: F401


class PrefixStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    RESERVED = "reserved", "Reserved"
    CONTAINER = "container", "Container"
    DEPRECATED = "deprecated", "Deprecated"


class Prefix(models.Model):
    """Hierarchical IP prefix on PG-native inet (ADR-0002).

    For strict CIDR notation, two prefixes either are equal or one contains
    the other — containment is exactly the hierarchy (§12), so the DB-level
    invariant is uniqueness of (VRF, prefix); the GiST inet_ops index makes
    containment/hierarchy queries fast at scale.
    """

    vrf = models.ForeignKey(VRF, on_delete=models.PROTECT, related_name="prefixes")
    prefix = CidrField()
    status = models.CharField(
        max_length=20, choices=PrefixStatus.choices, default=PrefixStatus.ACTIVE
    )
    tenant = models.ForeignKey(
        "organizations.Tenant",
        on_delete=models.PROTECT,
        related_name="prefixes",
        null=True,
        blank=True,
    )
    site = models.ForeignKey(
        "zipam_sites.Site",
        on_delete=models.PROTECT,
        related_name="prefixes",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vrf__name", "prefix"]
        constraints = [
            models.UniqueConstraint(fields=["vrf", "prefix"], name="uniq_prefix_per_vrf"),
        ]
        indexes = [
            # containment/hierarchy queries (>>, <<, <<=) — GiST inet_ops
            GistIndex(
                fields=["prefix"],
                opclasses=["inet_ops"],
                name="prefix_inet_gist",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.prefix} ({self.vrf.name})"

    def clean(self) -> None:
        super().clean()
        value = str(self.prefix or "")
        if "/" not in value:
            raise ValidationError(
                {"prefix": "Prefix must be in CIDR notation, e.g. 10.0.0.0/24."}
            )
        try:
            ipaddress.ip_network(value, strict=True)
        except ValueError as exc:
            raise ValidationError({"prefix": str(exc)}) from exc

    # ------------------------------------------------------------------ hierarchy

    @property
    def network(self) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
        return ipaddress.ip_network(str(self.prefix))

    def overlaps(self) -> QuerySet[Prefix]:
        return Prefix.objects.filter(vrf=self.vrf, prefix__net_overlap=self.prefix).exclude(
            pk=self.pk
        )

    def get_parent(self) -> Prefix | None:
        """Closest containing prefix, resolved by DB containment (§12)."""
        return (
            Prefix.objects.filter(vrf=self.vrf, prefix__net_contains_or_equals=self.prefix)
            .annotate(mask=MaskLen("prefix"))
            .exclude(pk=self.pk)
            .order_by("-mask")
            .first()
        )

    def children(self) -> QuerySet[Prefix]:
        return Prefix.objects.filter(vrf=self.vrf, prefix__net_contained=self.prefix)

    def immediate_children(self) -> QuerySet[Prefix]:
        """Children not nested inside another child — one DB pass, no Python walk."""
        from django.db.models import Exists, OuterRef

        intermediate = Prefix.objects.filter(
            vrf=OuterRef("vrf"),
            prefix__net_contained=self.prefix,
            prefix__net_contains=OuterRef("prefix"),
        ).exclude(pk=OuterRef("pk"))
        return self.children().exclude(Exists(intermediate))

    def ancestor_of(self, other: Prefix) -> bool:
        return (
            self.vrf_id == other.vrf_id
            and Prefix.objects.filter(pk=self.pk, prefix__net_contains=other.prefix).exists()
        )

    # ------------------------------------------------------------------ metrics

    def utilization(self) -> dict[str, int | float]:
        from apps.prefixes import services

        return services.calculate_utilization(self)
