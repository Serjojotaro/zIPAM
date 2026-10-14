# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from django.db import models

GLOBAL_VRF_NAME = "global"


class VRF(models.Model):
    """Routing table container; prefixes/addresses are unique per VRF (§10, ADR-0002)."""

    name = models.CharField(max_length=255, unique=True)
    rd = models.CharField(
        "route distinguisher", max_length=64, blank=True, default="",
        help_text="Optional route distinguisher, e.g. 65000:100.",
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "VRF"
        verbose_name_plural = "VRFs"

    def __str__(self) -> str:
        return self.name
