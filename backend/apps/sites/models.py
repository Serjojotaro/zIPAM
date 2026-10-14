# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "regions"

    def __str__(self) -> str:
        return self.name


class Site(models.Model):
    name = models.CharField(max_length=255, unique=True)
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="sites", null=True, blank=True
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["region__name", "name"]

    def __str__(self) -> str:
        return self.name
