# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.db import models


class Organization(models.Model):
    """Top-level ownership container (§10)."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Tenant(models.Model):
    """Customer/department inside an organization."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="tenants")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["organization__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="uniq_tenant_name_per_org"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.organization.name}/{self.name}"
