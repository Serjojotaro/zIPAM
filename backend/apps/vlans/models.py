# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class VLAN(models.Model):
    """802.1Q broadcast domain (§10). vid is unique per logical name, not globally:
    the same vid may exist for different networks."""

    name = models.CharField(max_length=255)
    vid = models.PositiveIntegerField(
        "VID", validators=[MinValueValidator(1), MaxValueValidator(4094)]
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vid", "name"]
        constraints = [
            models.UniqueConstraint(fields=["vid", "name"], name="uniq_vlan_vid_name"),
        ]

    def __str__(self) -> str:
        return f"{self.vid} ({self.name})"
